# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            api_key TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'free',
            quota_limit INTEGER DEFAULT 100,
            quota_used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA-256 and a static salt."""
    salt = b"englisp_salt_12345"
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches the stored hash."""
    return hash_password(plain_password) == hashed_password

def generate_api_key() -> str:
    """Generates a secure, random API key prefixed with 'englisp_live_'."""
    return "englisp_live_" + secrets.token_urlsafe(32)

def create_user(email: str, password_hash: str = None) -> Optional[dict]:
    """Creates a new user with a generated API key."""
    api_key = generate_api_key()
    created_at = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, api_key, created_at) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), password_hash, api_key, created_at)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieves a user record by email address."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_api_key(api_key: str) -> Optional[dict]:
    """Retrieves a user record by their API key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE api_key = ?", (api_key.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def increment_user_quota(user_id: int, amount: int = 1):
    """Increments the quota count for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET quota_used = quota_used + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_user_tier(email: str, tier: str, quota_limit: int):
    """Updates a user's tier and monthly quota limit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tier = ?, quota_limit = ? WHERE email = ?", (tier, quota_limit, email.lower().strip()))
    conn.commit()
    conn.close()
