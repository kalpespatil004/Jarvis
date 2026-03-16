"""
vault/vault_manager.py
-----------------------
High-level Vault: store, retrieve, list encrypted documents.
Uses local SQLite database for persistence.
"""

import sqlite3
import os
import json
from datetime import datetime

try:
    from config import VAULT_DB_PATH
except ImportError:
    VAULT_DB_PATH = "database/vault.db"

# Master password (set via vault/auth.py in production)
_MASTER_PASSWORD = "jarvis_vault_default"


def _get_conn():
    os.makedirs(os.path.dirname(VAULT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(VAULT_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT UNIQUE NOT NULL,
            data      TEXT NOT NULL,
            tags      TEXT DEFAULT '[]',
            created   TEXT NOT NULL,
            modified  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def store_document(name: str, content: str, tags: list = None, password: str = None) -> str:
    """Store an encrypted document."""
    if not name or not content:
        return "❌ Name and content are required."
    try:
        from vault.encrypt import encrypt
        pwd = password or _MASTER_PASSWORD
        encrypted = encrypt(content, pwd)

        now = datetime.now().isoformat()
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO vault (name, data, tags, created, modified)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    data=excluded.data, tags=excluded.tags, modified=excluded.modified
            """, (name, encrypted, json.dumps(tags or []), now, now))
        return f"🔐 Document '{name}' stored securely."
    except Exception as e:
        return f"❌ Vault store error: {e}"


def retrieve_document(name: str, password: str = None) -> str:
    """Retrieve and decrypt a document."""
    if not name:
        return "❌ Document name required."
    try:
        from vault.encrypt import decrypt
        pwd = password or _MASTER_PASSWORD
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM vault WHERE name=?", (name,)
            ).fetchone()
        if not row:
            return f"❌ Document '{name}' not found in vault."
        return decrypt(row[0], pwd)
    except Exception as e:
        return f"❌ Vault retrieve error: {e}"


def list_documents() -> list:
    """List all document names in the vault."""
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT name, created FROM vault ORDER BY created DESC"
            ).fetchall()
        return [f"{r[0]} (saved: {r[1][:10]})" for r in rows]
    except Exception:
        return []


def delete_document(name: str) -> str:
    """Delete a document from the vault."""
    try:
        with _get_conn() as conn:
            conn.execute("DELETE FROM vault WHERE name=?", (name,))
        return f"🗑 Document '{name}' deleted from vault."
    except Exception as e:
        return f"❌ Delete error: {e}"
