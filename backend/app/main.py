from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .database import Base, SessionLocal, engine

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="MoneyTrack API")


def run_dev_migrations() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()"
            )
        )
        conn.execute(
            text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tx_date DATE")
        )
        conn.execute(
            text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS category_id INTEGER")
        )
        conn.execute(
            text(
                "UPDATE transactions SET tx_date = COALESCE(tx_date, DATE(created_at), CURRENT_DATE)"
            )
        )
        conn.execute(
            text("ALTER TABLE transactions ALTER COLUMN tx_date SET NOT NULL")
        )


run_dev_migrations()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    token_data = auth.decode_access_token(token)
    if token_data is None or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = (
        db.query(models.User)
        .filter(models.User.username == token_data.username)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def _period_start(period: str) -> date:
    today = date.today()
    days_map = {"week": 7, "month": 30, "year": 365}
    return today - timedelta(days=days_map[period])


def _tx_to_response(tx: models.Transaction) -> schemas.TransactionResponse:
    return schemas.TransactionResponse(
        id=tx.id,
        amount=tx.amount,
        type=tx.type,
        category_id=tx.category_id,
        category_name=tx.category.name if tx.category else None,
        description=tx.description,
        tx_date=tx.tx_date,
        created_at=tx.created_at,
    )


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = models.User(
        username=user.username,
        hashed_password=auth.get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = auth.create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/categories", response_model=list[schemas.CategoryResponse])
def get_categories(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Category)
        .filter(models.Category.owner_id == current_user.id)
        .order_by(models.Category.name.asc())
        .all()
    )


@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    name = category.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    existing = (
        db.query(models.Category)
        .filter(models.Category.owner_id == current_user.id)
        .filter(func.lower(models.Category.name) == name.lower())
        .first()
    )
    if existing:
        return existing

    db_category = models.Category(name=name, owner_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/transactions", response_model=list[schemas.TransactionResponse])
def get_transactions(
    period: str | None = Query(None, enum=["week", "month", "year"]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = (
        db.query(models.Transaction)
        .filter(models.Transaction.owner_id == current_user.id)
        .order_by(models.Transaction.tx_date.desc(), models.Transaction.id.desc())
    )

    if period:
        query = query.filter(models.Transaction.tx_date >= _period_start(period))

    return [_tx_to_response(tx) for tx in query.all()]


@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    category_id = payload.category_id
    category_name = "Uncategorized"
    if category_id is not None:
        category = (
            db.query(models.Category)
            .filter(models.Category.id == category_id)
            .filter(models.Category.owner_id == current_user.id)
            .first()
        )
        if category is None:
            raise HTTPException(status_code=400, detail="Category not found")
        category_name = category.name

    tx = models.Transaction(
        amount=payload.amount,
        type=payload.type,
        category_legacy=category_name,
        category_id=category_id,
        description=(payload.description or "").strip(),
        tx_date=payload.tx_date,
        owner_id=current_user.id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return _tx_to_response(tx)


@app.post("/income", response_model=schemas.TransactionResponse)
def add_income(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    payload.type = "income"
    return create_transaction(payload, db, current_user)


@app.post("/expense", response_model=schemas.TransactionResponse)
def add_expense(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    payload.type = "expense"
    return create_transaction(payload, db, current_user)


@app.get("/analytics", response_model=schemas.AnalyticsSummary)
def get_analytics(
    period: str = Query("month", enum=["week", "month", "year"]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    start_date = _period_start(period)

    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.owner_id == current_user.id)
        .filter(models.Transaction.tx_date >= start_date)
        .all()
    )

    income = sum(tx.amount for tx in transactions if tx.type == "income")
    expense = sum(tx.amount for tx in transactions if tx.type == "expense")
    return schemas.AnalyticsSummary(income=income, expense=expense, balance=income - expense)


@app.get("/analytics/categories", response_model=list[schemas.CategoryStat])
def get_category_stats(
    period: str = Query("month", enum=["week", "month", "year"]),
    tx_type: str | None = Query(None, enum=["income", "expense"]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    start_date = _period_start(period)

    query = (
        db.query(models.Category.name, func.sum(models.Transaction.amount).label("total"))
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(models.Transaction.owner_id == current_user.id)
        .filter(models.Transaction.tx_date >= start_date)
    )

    if tx_type:
        query = query.filter(models.Transaction.type == tx_type)

    rows = query.group_by(models.Category.name).order_by(func.sum(models.Transaction.amount).desc()).all()

    return [schemas.CategoryStat(name=name, total=float(total or 0)) for name, total in rows]


@app.get("/analytics/timeline", response_model=list[schemas.TimelinePoint])
def get_timeline(
    period: str = Query("month", enum=["week", "month", "year"]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    start_date = _period_start(period)

    income_case = case((models.Transaction.type == "income", models.Transaction.amount), else_=0)
    expense_case = case((models.Transaction.type == "expense", models.Transaction.amount), else_=0)

    rows = (
        db.query(
            models.Transaction.tx_date.label("date"),
            func.sum(income_case).label("income"),
            func.sum(expense_case).label("expense"),
        )
        .filter(models.Transaction.owner_id == current_user.id)
        .filter(models.Transaction.tx_date >= start_date)
        .group_by(models.Transaction.tx_date)
        .order_by(models.Transaction.tx_date.asc())
        .all()
    )

    result: list[schemas.TimelinePoint] = []
    for row in rows:
        income = float(row.income or 0)
        expense = float(row.expense or 0)
        result.append(
            schemas.TimelinePoint(
                date=row.date,
                income=income,
                expense=expense,
                net=income - expense,
            )
        )

    return result
