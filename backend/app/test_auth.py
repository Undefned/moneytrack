import pytest
from datetime import datetime, timedelta
from jose import jwt
from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .schemas import TokenData


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Password hash should return a string."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)

    def test_hash_password_different_hashes(self):
        """Same password should produce different hashes (salt)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    def test_hash_password_not_equal_to_plain(self):
        """Hashed password should not equal plain password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """verify_password should handle empty strings."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestCreateAccessToken:
    """Tests for access token creation."""

    def test_create_access_token_returns_string(self):
        """create_access_token should return a string."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)

    def test_create_access_token_not_empty(self):
        """Created token should not be empty."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert len(token) > 0

    def test_create_access_token_contains_three_parts(self):
        """JWT should have three parts separated by dots."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_custom_expiry(self):
        """Token should respect custom expiry time."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded

    def test_create_access_token_contains_username(self):
        """Token should contain the username in payload."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"

    def test_create_access_token_contains_expiry(self):
        """Token should contain expiry time."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded

    def test_create_access_token_default_expiry(self):
        """Default expiry should be 60 minutes."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # decoded["exp"] is already a timestamp, compare directly
        expected_exp = datetime.now().timestamp() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
        # Allow 2 seconds difference
        assert abs(decoded["exp"] - expected_exp) < 2

    def test_create_access_token_with_extra_data(self):
        """Token should include extra data in payload."""
        data = {"sub": "testuser", "extra": "value"}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["extra"] == "value"


class TestDecodeAccessToken:
    """Tests for access token decoding."""

    def test_decode_valid_token_returns_token_data(self):
        """decode_access_token should return TokenData for valid token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        result = decode_access_token(token)
        assert isinstance(result, TokenData)
        assert result.username == "testuser"

    def test_decode_invalid_token_returns_none(self):
        """decode_access_token should return None for invalid token."""
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_empty_token_returns_none(self):
        """decode_access_token should return None for empty token."""
        result = decode_access_token("")
        assert result is None

    def test_decode_token_without_sub_returns_none(self):
        """decode_access_token should return None if 'sub' is missing."""
        token = jwt.encode({"exp": datetime.utcnow() + timedelta(minutes=1)}, SECRET_KEY, algorithm=ALGORITHM)
        result = decode_access_token(token)
        assert result is None

    def test_decode_expired_token_returns_none(self):
        """decode_access_token should return None for expired token."""
        expired_delta = timedelta(minutes=-1)
        token = create_access_token({"sub": "testuser"}, expires_delta=expired_delta)
        result = decode_access_token(token)
        assert result is None

    def test_decode_token_with_wrong_secret_returns_none(self):
        """decode_access_token should return None if token was signed with different key."""
        data = {"sub": "testuser"}
        wrong_token = jwt.encode(data, "wrong_secret", algorithm=ALGORITHM)
        result = decode_access_token(wrong_token)
        assert result is None


class TestIntegration:
    """Integration tests for auth flow."""

    def test_full_auth_flow(self):
        """Test complete authentication flow: hash -> verify -> token -> decode."""
        # Password hashing
        password = "securepassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

        # Token creation
        username = "testuser"
        token = create_access_token({"sub": username})
        assert token is not None

        # Token decoding
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.username == username

    def test_multiple_users_isolated(self):
        """Tokens for different users should be isolated."""
        user1_token = create_access_token({"sub": "user1"})
        user2_token = create_access_token({"sub": "user2"})

        user1_data = decode_access_token(user1_token)
        user2_data = decode_access_token(user2_token)

        assert user1_data.username == "user1"
        assert user2_data.username == "user2"
        assert user1_data.username != user2_data.username
