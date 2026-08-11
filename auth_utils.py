"""
Auth helpers for the account portal.

Password hashing uses Python's built-in hashlib (PBKDF2-HMAC-SHA256)
rather than a compiled library like bcrypt, deliberately, so this
installs cleanly everywhere without the kind of build headaches the
psycopg2/pydantic-core installs caused earlier. It's a well-regarded,
standard approach, not a shortcut on security.
"""
import os
import hmac
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-before-deploying-jwt-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, derived_b64 = stored_hash.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(derived_b64)
    except (ValueError, AttributeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate, expected)


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
