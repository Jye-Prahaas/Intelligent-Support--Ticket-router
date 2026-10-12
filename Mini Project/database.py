
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("TICKET_ROUTER_DB", str(BASE_DIR / "support_ticket_router.db")))
KEY_PATH = Path(os.getenv("PII_VAULT_KEY_FILE", str(BASE_DIR / "vault.key")))


def _get_fernet() -> Fernet:
    """Load a key from the environment or create a local demo key file."""
    env_key = os.getenv("PII_VAULT_KEY")
    if env_key:
        key = env_key.encode("utf-8")
    else:
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not KEY_PATH.exists():
            KEY_PATH.write_bytes(Fernet.generate_key())
            try:
                KEY_PATH.chmod(0o600)
            except OSError:
                pass
        key = KEY_PATH.read_bytes().strip()
    try:
        return Fernet(key)
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "Invalid PII vault key. Set PII_VAULT_KEY to a valid Fernet key or remove the local vault.key to regenerate a demo key."
        ) from exc


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                masked_text TEXT NOT NULL,
                primary_label TEXT NOT NULL,
                sub_label TEXT NOT NULL,
                sentiment REAL NOT NULL,
                priority_score REAL NOT NULL,
                target_tier TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pii_vault (
                vault_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                token TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_pii_vault_ticket_id
                ON pii_vault(ticket_id);

            CREATE TABLE IF NOT EXISTS vault_access_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                accessed_at TEXT NOT NULL
            );
            """
        )


def save_ticket(
    *, ticket_id: str, masked_text: str, primary_label: str, sub_label: str,
    sentiment: float, priority_score: float, target_tier: str,
    pii_vault: dict[str, list[str]] | None = None,
) -> None:
    """Save masked ticket and encrypt any detected original values."""
    now = datetime.now(timezone.utc).isoformat()
    pii_vault = pii_vault or {}
    fernet = _get_fernet() if any(pii_vault.values()) else None

    with _connect() as conn:
        conn.execute(
            """INSERT INTO tickets
               (ticket_id, masked_text, primary_label, sub_label, sentiment,
                priority_score, target_tier, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticket_id, masked_text, primary_label, sub_label, sentiment,
             priority_score, target_tier, now),
        )
        if fernet:
            for pii_type, values in pii_vault.items():
                for value in values:
                    if not value or not value.strip():
                        continue
                    encrypted = fernet.encrypt(value.strip().encode("utf-8"))
                    conn.execute(
                        """INSERT INTO pii_vault
                           (ticket_id, token, pii_type, encrypted_value, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (ticket_id, pii_type, pii_type.strip("[]"), encrypted, now),
                    )


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """SELECT ticket_id, masked_text, primary_label, sub_label,
                      sentiment, priority_score, target_tier, created_at
               FROM tickets WHERE ticket_id = ?""",
            (ticket_id,),
        ).fetchone()
    return dict(row) if row else None


def retrieve_pii(ticket_id: str, *, actor: str = "vault-admin") -> list[dict[str, str]]:
    """Decrypt PII only for use behind the separately authenticated API route."""
    fernet = _get_fernet()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT vault_id, token, pii_type, encrypted_value FROM pii_vault WHERE ticket_id = ? ORDER BY vault_id",
            (ticket_id,),
        ).fetchall()
        conn.execute(
            "INSERT INTO vault_access_logs (ticket_id, actor, action, status, accessed_at) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, actor, "retrieve_pii", "success" if rows else "no_records",
             datetime.now(timezone.utc).isoformat()),
        )
    output: list[dict[str, str]] = []
    for row in rows:
        try:
            value = fernet.decrypt(bytes(row["encrypted_value"])).decode("utf-8")
        except (InvalidToken, ValueError) as exc:
            raise RuntimeError("Could not decrypt vault record. Check that the original encryption key is being used.") from exc
        output.append({"vault_id": str(row["vault_id"]), "token": row["token"], "pii_type": row["pii_type"], "value": value})
    return output


def log_vault_access(ticket_id: str, actor: str, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO vault_access_logs (ticket_id, actor, action, status, accessed_at) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, actor, "retrieve_pii", status, datetime.now(timezone.utc).isoformat()),
        )
