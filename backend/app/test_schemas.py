import pytest
from datetime import date, datetime
from pydantic import ValidationError
from .schemas import (
    UserCreate,
    UserResponse,
    Token,
    TokenData,
    CategoryCreate,
    CategoryResponse,
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    AnalyticsSummary,
    CategoryStat,
    TimelinePoint,
)


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        """Should create valid UserCreate."""
        user = UserCreate(username="testuser", password="password123")
        assert user.username == "testuser"
        assert user.password == "password123"

    def test_user_create_empty_password(self):
        """Should accept empty password (validation at service level)."""
        user = UserCreate(username="testuser", password="")
        assert user.password == ""

    def test_user_create_long_username(self):
        """Should accept long usernames."""
        user = UserCreate(username="a" * 100, password="pass")
        assert len(user.username) == 100

    def test_user_create_special_chars(self):
        """Should accept special characters in username."""
        user = UserCreate(username="test@user.com", password="pass")
        assert user.username == "test@user.com"


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Should create valid UserResponse."""
        user = UserResponse(id=1, username="testuser")
        assert user.id == 1
        assert user.username == "testuser"

    def test_user_response_negative_id(self):
        """Should accept negative id."""
        user = UserResponse(id=-1, username="testuser")
        assert user.id == -1

    def test_user_response_zero_id(self):
        """Should accept zero id."""
        user = UserResponse(id=0, username="testuser")
        assert user.id == 0


class TestToken:
    """Tests for Token schema."""

    def test_valid_token(self):
        """Should create valid Token."""
        token = Token(access_token="abc123", token_type="bearer")
        assert token.access_token == "abc123"
        assert token.token_type == "bearer"

    def test_token_empty_access_token(self):
        """Should accept empty access_token."""
        token = Token(access_token="", token_type="bearer")
        assert token.access_token == ""

    def test_token_type_case(self):
        """Token type should preserve case."""
        token = Token(access_token="abc", token_type="Bearer")
        assert token.token_type == "Bearer"


class TestTokenData:
    """Tests for TokenData schema."""

    def test_valid_token_data(self):
        """Should create valid TokenData."""
        data = TokenData(username="testuser")
        assert data.username == "testuser"

    def test_token_data_none(self):
        """Should accept None username."""
        data = TokenData(username=None)
        assert data.username is None

    def test_token_data_default(self):
        """Should default to None username."""
        data = TokenData()
        assert data.username is None


class TestCategoryCreate:
    """Tests for CategoryCreate schema."""

    def test_valid_category_create(self):
        """Should create valid CategoryCreate."""
        cat = CategoryCreate(name="Food")
        assert cat.name == "Food"

    def test_category_create_empty_name(self):
        """Should accept empty name."""
        cat = CategoryCreate(name="")
        assert cat.name == ""

    def test_category_create_long_name(self):
        """Should accept long names."""
        cat = CategoryCreate(name="a" * 200)
        assert len(cat.name) == 200

    def test_category_create_special_chars(self):
        """Should accept special characters."""
        cat = CategoryCreate(name="Food & Drinks!")
        assert cat.name == "Food & Drinks!"


class TestCategoryResponse:
    """Tests for CategoryResponse schema."""

    def test_valid_category_response(self):
        """Should create valid CategoryResponse."""
        cat = CategoryResponse(id=1, name="Food")
        assert cat.id == 1
        assert cat.name == "Food"

    def test_category_response_negative_id(self):
        """Should accept negative id."""
        cat = CategoryResponse(id=-1, name="Food")
        assert cat.id == -1


class TestTransactionBase:
    """Tests for TransactionBase schema."""

    def test_valid_transaction_income(self):
        """Should create valid income transaction."""
        tx = TransactionBase(amount=100.0, type="income", tx_date=date.today())
        assert tx.amount == 100.0
        assert tx.type == "income"

    def test_valid_transaction_expense(self):
        """Should create valid expense transaction."""
        tx = TransactionBase(amount=50.0, type="expense", tx_date=date.today())
        assert tx.amount == 50.0
        assert tx.type == "expense"

    def test_transaction_invalid_type(self):
        """Should reject invalid type."""
        with pytest.raises(ValidationError):
            TransactionBase(amount=100.0, type="invalid", tx_date=date.today())

    def test_transaction_negative_amount(self):
        """Should accept negative amount."""
        tx = TransactionBase(amount=-50.0, type="expense", tx_date=date.today())
        assert tx.amount == -50.0

    def test_transaction_zero_amount(self):
        """Should accept zero amount."""
        tx = TransactionBase(amount=0.0, type="income", tx_date=date.today())
        assert tx.amount == 0.0

    def test_transaction_with_category_id(self):
        """Should accept category_id."""
        tx = TransactionBase(amount=100.0, type="income", tx_date=date.today(), category_id=1)
        assert tx.category_id == 1

    def test_transaction_without_category_id(self):
        """Should work without category_id."""
        tx = TransactionBase(amount=100.0, type="income", tx_date=date.today())
        assert tx.category_id is None

    def test_transaction_with_description(self):
        """Should accept description."""
        tx = TransactionBase(amount=100.0, type="income", tx_date=date.today(), description="Test")
        assert tx.description == "Test"

    def test_transaction_without_description(self):
        """Should work without description."""
        tx = TransactionBase(amount=100.0, type="income", tx_date=date.today())
        assert tx.description is None

    def test_transaction_missing_required(self):
        """Should reject missing required fields."""
        with pytest.raises(ValidationError):
            TransactionBase(type="income", tx_date=date.today())

    def test_transaction_float_amount(self):
        """Should accept float amount."""
        tx = TransactionBase(amount=99.99, type="expense", tx_date=date.today())
        assert tx.amount == 99.99


class TestTransactionCreate:
    """Tests for TransactionCreate schema."""

    def test_valid_transaction_create(self):
        """Should create valid TransactionCreate."""
        tx = TransactionCreate(amount=100.0, type="income", tx_date=date.today())
        assert tx.amount == 100.0
        assert tx.type == "income"

    def test_transaction_create_all_fields(self):
        """Should accept all optional fields."""
        tx = TransactionCreate(
            amount=100.0,
            type="expense",
            tx_date=date.today(),
            category_id=5,
            description="Test description"
        )
        assert tx.amount == 100.0
        assert tx.type == "expense"
        assert tx.category_id == 5
        assert tx.description == "Test description"


class TestTransactionResponse:
    """Tests for TransactionResponse schema."""

    def test_valid_transaction_response(self):
        """Should create valid TransactionResponse."""
        tx = TransactionResponse(
            id=1,
            amount=100.0,
            type="income",
            tx_date=date.today(),
            created_at=datetime.now(),
            category_name=None
        )
        assert tx.id == 1
        assert tx.amount == 100.0

    def test_transaction_response_with_category(self):
        """Should accept category_name."""
        tx = TransactionResponse(
            id=1,
            amount=50.0,
            type="expense",
            tx_date=date.today(),
            created_at=datetime.now(),
            category_name="Food"
        )
        assert tx.category_name == "Food"

    def test_transaction_response_without_category(self):
        """Should work without category_name."""
        tx = TransactionResponse(
            id=1,
            amount=50.0,
            type="expense",
            tx_date=date.today(),
            created_at=datetime.now()
        )
        assert tx.category_name is None


class TestAnalyticsSummary:
    """Tests for AnalyticsSummary schema."""

    def test_valid_analytics_summary(self):
        """Should create valid AnalyticsSummary."""
        summary = AnalyticsSummary(income=1000.0, expense=500.0, balance=500.0)
        assert summary.income == 1000.0
        assert summary.expense == 500.0
        assert summary.balance == 500.0

    def test_analytics_summary_negative_balance(self):
        """Should accept negative balance."""
        summary = AnalyticsSummary(income=100.0, expense=500.0, balance=-400.0)
        assert summary.balance == -400.0

    def test_analytics_summary_zero(self):
        """Should accept zero values."""
        summary = AnalyticsSummary(income=0.0, expense=0.0, balance=0.0)
        assert summary.income == 0.0
        assert summary.expense == 0.0
        assert summary.balance == 0.0

    def test_analytics_summary_float(self):
        """Should accept float values."""
        summary = AnalyticsSummary(income=999.99, expense=111.11, balance=888.88)
        assert summary.income == 999.99


class TestCategoryStat:
    """Tests for CategoryStat schema."""

    def test_valid_category_stat(self):
        """Should create valid CategoryStat."""
        stat = CategoryStat(name="Food", total=500.0)
        assert stat.name == "Food"
        assert stat.total == 500.0

    def test_category_stat_negative_total(self):
        """Should accept negative total."""
        stat = CategoryStat(name="Refund", total=-100.0)
        assert stat.total == -100.0

    def test_category_stat_zero_total(self):
        """Should accept zero total."""
        stat = CategoryStat(name="Unused", total=0.0)
        assert stat.total == 0.0


class TestTimelinePoint:
    """Tests for TimelinePoint schema."""

    def test_valid_timeline_point(self):
        """Should create valid TimelinePoint."""
        point = TimelinePoint(
            date=date.today(),
            income=100.0,
            expense=50.0,
            net=50.0
        )
        assert point.date == date.today()
        assert point.income == 100.0
        assert point.expense == 50.0
        assert point.net == 50.0

    def test_timeline_point_negative_net(self):
        """Should accept negative net."""
        point = TimelinePoint(
            date=date.today(),
            income=50.0,
            expense=100.0,
            net=-50.0
        )
        assert point.net == -50.0

    def test_timeline_point_zero(self):
        """Should accept zero values."""
        point = TimelinePoint(
            date=date.today(),
            income=0.0,
            expense=0.0,
            net=0.0
        )
        assert point.income == 0.0
        assert point.expense == 0.0
        assert point.net == 0.0


class TestSchemaIntegration:
    """Integration tests for schemas."""

    def test_user_create_to_response_flow(self):
        """Test UserCreate -> UserResponse flow."""
        create_data = UserCreate(username="newuser", password="pass123")
        # Simulate DB response
        response = UserResponse(id=1, username=create_data.username)
        assert response.username == create_data.username

    def test_transaction_full_flow(self):
        """Test TransactionCreate -> TransactionResponse flow."""
        create_data = TransactionCreate(
            amount=200.0,
            type="income",
            tx_date=date.today(),
            category_id=1,
            description="Salary"
        )
        # Simulate DB response
        response = TransactionResponse(
            id=1,
            amount=create_data.amount,
            type=create_data.type,
            tx_date=create_data.tx_date,
            created_at=datetime.now(),
            category_name="Work"
        )
        assert response.amount == create_data.amount
        assert response.type == create_data.type

    def test_analytics_calculation(self):
        """Test analytics summary calculation."""
        income = 1500.0
        expense = 800.0
        summary = AnalyticsSummary(income=income, expense=expense, balance=income - expense)
        assert summary.balance == income - expense

    def test_category_stats_list(self):
        """Test list of category stats."""
        stats = [
            CategoryStat(name="Food", total=300.0),
            CategoryStat(name="Transport", total=150.0),
            CategoryStat(name="Entertainment", total=100.0)
        ]
        total_expense = sum(s.total for s in stats)
        assert total_expense == 550.0

    def test_timeline_points_sorted(self):
        """Test timeline points can be sorted by date."""
        points = [
            TimelinePoint(date=date(2024, 1, 3), income=100, expense=50, net=50),
            TimelinePoint(date=date(2024, 1, 1), income=200, expense=100, net=100),
            TimelinePoint(date=date(2024, 1, 2), income=150, expense=75, net=75)
        ]
        sorted_points = sorted(points, key=lambda p: p.date)
        assert sorted_points[0].date == date(2024, 1, 1)
        assert sorted_points[1].date == date(2024, 1, 2)
        assert sorted_points[2].date == date(2024, 1, 3)
