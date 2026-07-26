import logging
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)


# ==========================================================
# Constants
# ==========================================================

ALGORITHM = "HS256"

EMAIL_VERIFY_EXPIRE_HOURS = 24

PASSWORD_RESET_EXPIRE_MINUTES = 30


# ==========================================================
# Password Hashing
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================================
# Create Access Token
# ==========================================================

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


# ==========================================================
# Create Refresh Token
# ==========================================================

def create_refresh_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=ALGORITHM)


# ==========================================================
# Email Verification Token
# ==========================================================

def create_email_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=EMAIL_VERIFY_EXPIRE_HOURS
    )
    payload = {
        "email": email,
        "type": "verify",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


# ==========================================================
# Password Reset Token
# ==========================================================

def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=PASSWORD_RESET_EXPIRE_MINUTES
    )
    payload = {
        "email": email,
        "type": "reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


# ==========================================================
# Verify Token (returns payload or None)
# Validates signature + expiry only.
# Callers MUST check payload["type"] themselves.
# ==========================================================

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None


# ==========================================================
# Verify Refresh Token
# ==========================================================

def verify_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None


# ==========================================================
# Decode Token (raises JWTError on failure)
# Used by protected route dependencies.
# ==========================================================

def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
    )


# ==========================================================
# Token Type Helpers
# ==========================================================

def is_access_token(payload: dict) -> bool:
    return payload.get("type") == "access"


def is_refresh_token(payload: dict) -> bool:
    return payload.get("type") == "refresh"


def is_verify_token(payload: dict) -> bool:
    return payload.get("type") == "verify"


def is_reset_token(payload: dict) -> bool:
    return payload.get("type") == "reset"
