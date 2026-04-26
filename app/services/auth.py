import hashlib
import hmac
import os
import secrets
from base64 import b64decode, b64encode

from app.db import get_connection


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{b64encode(salt).decode()}${b64encode(digest).decode()}"


def verify_password(password: str, stored_value: str | None) -> bool:
    if not stored_value or "$" not in stored_value:
        return False

    salt_b64, digest_b64 = stored_value.split("$", 1)
    salt = b64decode(salt_b64.encode())
    expected_digest = b64decode(digest_b64.encode())
    candidate_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return hmac.compare_digest(candidate_digest, expected_digest)


def create_user(name: str, email: str, password: str) -> tuple[bool, str]:
    password_hash = hash_password(password)
    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash),
            )
    except Exception:
        return False, "User already exists with this email."
    return True, "Registration successful. Please log in."


def authenticate_user(email: str, password: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def get_user_by_id(user_id: int | None) -> dict | None:
    if not user_id:
        return None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def upsert_google_user(google_sub: str, email: str, name: str) -> dict:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id, name, email FROM users WHERE google_sub = ? OR email = ?",
            (google_sub, normalized_email),
        ).fetchone()
        if existing:
            connection.execute(
                "UPDATE users SET name = ?, email = ?, google_sub = ? WHERE id = ?",
                (name.strip(), normalized_email, google_sub, existing["id"]),
            )
            return {"id": existing["id"], "name": name.strip(), "email": normalized_email}

        cursor = connection.execute(
            "INSERT INTO users (name, email, google_sub) VALUES (?, ?, ?)",
            (name.strip(), normalized_email, google_sub),
        )
        return {"id": cursor.lastrowid, "name": name.strip(), "email": normalized_email}


def google_oauth_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
