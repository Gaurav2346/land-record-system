"""SQLite persistence for land records and transfer history."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "land_records.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY,
                property_number TEXT NOT NULL UNIQUE,
                survey_number TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                location TEXT NOT NULL,
                area INTEGER NOT NULL,
                property_type TEXT NOT NULL,
                owner_wallet TEXT NOT NULL,
                document_hash TEXT,
                register_tx_hash TEXT NOT NULL,
                register_block_number INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transfer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                from_wallet TEXT NOT NULL,
                to_wallet TEXT NOT NULL,
                from_owner_name TEXT,
                to_owner_name TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                transferred_at TEXT NOT NULL,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            );

            CREATE INDEX IF NOT EXISTS idx_transfer_property
                ON transfer_history (property_id);
            """
        )


def insert_property(
    *,
    property_id: int,
    property_number: str,
    survey_number: str,
    owner_name: str,
    location: str,
    area: int,
    property_type: str,
    owner_wallet: str,
    document_hash: Optional[str],
    register_tx_hash: str,
    register_block_number: int,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO properties (
                id, property_number, survey_number, owner_name, location,
                area, property_type, owner_wallet, document_hash,
                register_tx_hash, register_block_number, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property_id,
                property_number,
                survey_number,
                owner_name,
                location,
                area,
                property_type,
                owner_wallet.lower(),
                document_hash,
                register_tx_hash,
                register_block_number,
                _utc_now(),
            ),
        )


def update_property_owner(
    *,
    property_id: int,
    owner_name: str,
    owner_wallet: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE properties
            SET owner_name = ?, owner_wallet = ?
            WHERE id = ?
            """,
            (owner_name, owner_wallet.lower(), property_id),
        )


def set_document_hash(property_id: int, document_hash: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE properties SET document_hash = ? WHERE id = ?",
            (document_hash, property_id),
        )


def get_property_by_id(property_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM properties WHERE id = ?",
            (property_id,),
        ).fetchone()
    return dict(row) if row else None


def get_property_by_number(property_number: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM properties WHERE property_number = ?",
            (property_number,),
        ).fetchone()
    return dict(row) if row else None


def count_properties() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM properties").fetchone()
    return int(row["c"])


def list_properties(
    *,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM properties ORDER BY id DESC"
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params = (limit, offset)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def count_transfers() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM transfer_history").fetchone()
    return int(row["c"])


def insert_transfer(
    *,
    property_id: int,
    from_wallet: str,
    to_wallet: str,
    from_owner_name: Optional[str],
    to_owner_name: str,
    tx_hash: str,
    block_number: int,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transfer_history (
                property_id, from_wallet, to_wallet, from_owner_name,
                to_owner_name, tx_hash, block_number, transferred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property_id,
                from_wallet.lower(),
                to_wallet.lower(),
                from_owner_name,
                to_owner_name,
                tx_hash,
                block_number,
                _utc_now(),
            ),
        )


def get_transfer_history(property_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM transfer_history
            WHERE property_id = ?
            ORDER BY id ASC
            """,
            (property_id,),
        ).fetchall()
    return [dict(row) for row in rows]
