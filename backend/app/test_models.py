import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import Base
from .models import User, Category, Transaction


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for tests."""
    user = User(username="testuser", hashed_password="hashed123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_category(db_session, sample_user):
    """Create a sample category for tests."""
    category = Category(name="Food", owner_id=sample_user.id)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db_session):
        """Should create a user successfully."""
        user = User(username="newuser", hashed_password="pass123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.hashed_password == "pass123"

    def test_user_id_is_primary_key(self, db_session):
        """User id should be auto-incremented primary key."""
        user1 = User(username="user1", hashed_password="pass1")
        user2 = User(username="user2", hashed_password="pass2")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        assert user1.id < user2.id

    def test_user_username_unique(self, db_session):
        """Username should be unique."""
        user1 = User(username="duplicate", hashed_password="pass1")
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username="duplicate", hashed_password="pass2")
        db_session.add(user2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_created_at_default(self, db_session):
        """created_at should be set automatically."""
        user = User(username="testuser", hashed_password="pass123")
        db_session.add(user)
        db_session.commit()
        
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_transactions_relationship(self, db_session, sample_user):
        """User should have transactions relationship."""
        transaction = Transaction(
            amount=100.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert len(sample_user.transactions) == 1
        assert sample_user.transactions[0].amount == 100.0

    def test_user_categories_relationship(self, db_session, sample_user):
        """User should have categories relationship."""
        category = Category(name="Test Category", owner_id=sample_user.id)
        db_session.add(category)
        db_session.commit()
        
        assert len(sample_user.categories) == 1
        assert sample_user.categories[0].name == "Test Category"

    def test_user_delete_cascades_to_transactions(self, db_session, sample_user):
        """Deleting user should delete all transactions."""
        transaction = Transaction(
            amount=50.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        db_session.delete(sample_user)
        db_session.commit()
        
        assert db_session.query(Transaction).filter_by(owner_id=sample_user.id).count() == 0

    def test_user_delete_cascades_to_categories(self, db_session, sample_user):
        """Deleting user should delete all categories."""
        category = Category(name="Test", owner_id=sample_user.id)
        db_session.add(category)
        db_session.commit()
        
        db_session.delete(sample_user)
        db_session.commit()
        
        assert db_session.query(Category).filter_by(owner_id=sample_user.id).count() == 0


class TestCategoryModel:
    """Tests for Category model."""

    def test_create_category(self, db_session, sample_user):
        """Should create a category successfully."""
        category = Category(name="Entertainment", owner_id=sample_user.id)
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        assert category.id is not None
        assert category.name == "Entertainment"
        assert category.owner_id == sample_user.id

    def test_category_id_is_primary_key(self, db_session, sample_user):
        """Category id should be auto-incremented primary key."""
        cat1 = Category(name="Cat1", owner_id=sample_user.id)
        cat2 = Category(name="Cat2", owner_id=sample_user.id)
        db_session.add_all([cat1, cat2])
        db_session.commit()
        
        assert cat1.id < cat2.id

    def test_category_created_at_default(self, db_session, sample_user):
        """created_at should be set automatically."""
        category = Category(name="Test", owner_id=sample_user.id)
        db_session.add(category)
        db_session.commit()
        
        assert category.created_at is not None
        assert isinstance(category.created_at, datetime)

    def test_category_owner_relationship(self, db_session, sample_user):
        """Category should have owner relationship."""
        category = Category(name="Test", owner_id=sample_user.id)
        db_session.add(category)
        db_session.commit()
        
        assert category.owner is not None
        assert category.owner.username == "testuser"

    def test_category_transactions_relationship(self, db_session, sample_category):
        """Category should have transactions relationship."""
        transaction = Transaction(
            amount=75.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_category.owner_id,
            category_id=sample_category.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert len(sample_category.transactions) == 1
        assert sample_category.transactions[0].amount == 75.0

    def test_category_requires_owner(self, db_session):
        """Category should require owner_id."""
        category = Category(name="NoOwner")
        db_session.add(category)
        with pytest.raises(Exception):
            db_session.commit()


class TestTransactionModel:
    """Tests for Transaction model."""

    def test_create_transaction(self, db_session, sample_user):
        """Should create a transaction successfully."""
        transaction = Transaction(
            amount=200.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.amount == 200.0
        assert transaction.type == "income"
        assert transaction.owner_id == sample_user.id

    def test_transaction_id_is_primary_key(self, db_session, sample_user):
        """Transaction id should be auto-incremented primary key."""
        tx1 = Transaction(amount=10.0, type="expense", tx_date=date.today(), owner_id=sample_user.id)
        tx2 = Transaction(amount=20.0, type="expense", tx_date=date.today(), owner_id=sample_user.id)
        db_session.add_all([tx1, tx2])
        db_session.commit()
        
        assert tx1.id < tx2.id

    def test_transaction_type_income(self, db_session, sample_user):
        """Transaction type should accept 'income'."""
        transaction = Transaction(
            amount=100.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.type == "income"

    def test_transaction_type_expense(self, db_session, sample_user):
        """Transaction type should accept 'expense'."""
        transaction = Transaction(
            amount=50.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.type == "expense"

    def test_transaction_created_at_default(self, db_session, sample_user):
        """created_at should be set automatically."""
        transaction = Transaction(
            amount=100.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)

    def test_transaction_with_category(self, db_session, sample_category):
        """Transaction should link to category."""
        transaction = Transaction(
            amount=30.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_category.owner_id,
            category_id=sample_category.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.category_id == sample_category.id
        assert transaction.category.name == "Food"

    def test_transaction_without_category(self, db_session, sample_user):
        """Transaction should work without category."""
        transaction = Transaction(
            amount=25.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id,
            category_id=None
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.category_id is None
        assert transaction.category is None

    def test_transaction_with_description(self, db_session, sample_user):
        """Transaction should accept description."""
        transaction = Transaction(
            amount=150.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id,
            description="Grocery shopping"
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.description == "Grocery shopping"

    def test_transaction_without_description(self, db_session, sample_user):
        """Transaction should work without description."""
        transaction = Transaction(
            amount=100.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.description is None or transaction.description == ""

    def test_transaction_owner_relationship(self, db_session, sample_user):
        """Transaction should have owner relationship."""
        transaction = Transaction(
            amount=500.0,
            type="income",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.owner is not None
        assert transaction.owner.username == "testuser"

    def test_transaction_requires_owner(self, db_session):
        """Transaction should require owner_id."""
        transaction = Transaction(
            amount=100.0,
            type="income",
            tx_date=date.today()
        )
        db_session.add(transaction)
        with pytest.raises(Exception):
            db_session.commit()

    def test_transaction_amount_float(self, db_session, sample_user):
        """Transaction amount should accept float values."""
        transaction = Transaction(
            amount=99.99,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.amount == 99.99

    def test_transaction_amount_negative(self, db_session, sample_user):
        """Transaction amount should accept negative values."""
        transaction = Transaction(
            amount=-50.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.amount == -50.0

    def test_transaction_legacy_category(self, db_session, sample_user):
        """Transaction should support legacy category field."""
        transaction = Transaction(
            amount=40.0,
            type="expense",
            tx_date=date.today(),
            owner_id=sample_user.id,
            category_legacy="OldCategory"
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.category_legacy == "OldCategory"


class TestModelIntegration:
    """Integration tests for model relationships."""

    def test_user_with_multiple_categories(self, db_session, sample_user):
        """User should have multiple categories."""
        cat1 = Category(name="Food", owner_id=sample_user.id)
        cat2 = Category(name="Transport", owner_id=sample_user.id)
        cat3 = Category(name="Entertainment", owner_id=sample_user.id)
        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()
        
        assert len(sample_user.categories) == 3

    def test_user_with_multiple_transactions(self, db_session, sample_user):
        """User should have multiple transactions."""
        for i in range(5):
            tx = Transaction(
                amount=100.0 * (i + 1),
                type="income",
                tx_date=date.today(),
                owner_id=sample_user.id
            )
            db_session.add(tx)
        db_session.commit()
        
        assert len(sample_user.transactions) == 5

    def test_category_with_multiple_transactions(self, db_session, sample_category):
        """Category should have multiple transactions."""
        for i in range(3):
            tx = Transaction(
                amount=50.0,
                type="expense",
                tx_date=date.today(),
                owner_id=sample_category.owner_id,
                category_id=sample_category.id
            )
            db_session.add(tx)
        db_session.commit()
        
        assert len(sample_category.transactions) == 3

    def test_full_user_category_transaction_flow(self, db_session):
        """Test complete flow: user -> categories -> transactions."""
        # Create user
        user = User(username="fulltest", hashed_password="pass123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create category
        category = Category(name="Salary", owner_id=user.id)
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        # Create transaction
        transaction = Transaction(
            amount=5000.0,
            type="income",
            tx_date=date.today(),
            owner_id=user.id,
            category_id=category.id
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        # Verify relationships
        assert user.categories[0] == category
        assert user.transactions[0] == transaction
        assert category.transactions[0] == transaction
        assert transaction.category == category
        assert transaction.owner == user
