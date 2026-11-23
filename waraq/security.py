"""Credential hashing and authentication operations."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from .config import DEMO_MODE
from .storage import db, init_db

PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
        if rounds < 100_000 or rounds > 2_000_000:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), rounds)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError, OverflowError):
        return False


def authenticate(username: str, password: str) -> dict | None:
    username = (username or "").strip()
    if not username or not password:
        return None
    with db() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, role, member_id FROM users WHERE username=? COLLATE NOCASE",
            (username,),
        ).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"], "role": row["role"], "member_id": row["member_id"]}
    return None


def reset_demo_accounts() -> None:
    """Reset sample logins in local demo mode only."""
    if not DEMO_MODE:
        raise RuntimeError("Demo account reset is disabled when WARAQ_DEMO_MODE=0.")
    init_db()
    demo_members = [(101, "Saif", "saif_101", "saif123"),
                    (102, "Rida", "rida_102", "rida123"),
                    (103, "Aws", "aws_103", "aws123")]
    with db() as connection:
        manager = connection.execute("SELECT id FROM users WHERE username='admin' COLLATE NOCASE").fetchone()
        if manager:
            connection.execute(
                "UPDATE users SET username='admin', password_hash=?, role='manager', member_id=NULL WHERE id=?",
                (hash_password("admin123"), manager["id"]),
            )
        else:
            connection.execute("INSERT INTO users(username,password_hash,role) VALUES ('admin',?,'manager')",
                               (hash_password("admin123"),))

        for member_id, name, username, password in demo_members:
            member = connection.execute("SELECT id FROM members WHERE id=?", (member_id,)).fetchone()
            if not member:
                connection.execute("INSERT INTO members(id,name) VALUES (?,?)", (member_id, name))
            linked = connection.execute("SELECT id FROM users WHERE member_id=?", (member_id,)).fetchone()
            if linked:
                connection.execute("UPDATE users SET username=?, password_hash=?, role='member' WHERE id=?",
                                   (username, hash_password(password), linked["id"]))
            else:
                connection.execute("INSERT INTO users(username,password_hash,role,member_id) VALUES (?,?, 'member', ?)",
                                   (username, hash_password(password), member_id))


def change_password(username: str, current_password: str, new_password: str) -> None:
    if len(new_password) < 8:
        raise ValueError("كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل.")
    with db() as connection:
        row = connection.execute("SELECT id,password_hash FROM users WHERE username=? COLLATE NOCASE", (username,)).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            raise ValueError("كلمة المرور الحالية غير صحيحة.")
        connection.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_password), row["id"]))
