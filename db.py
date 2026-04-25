import sqlite3
from dataclasses import dataclass
from typing import Optional

DB_PATH = "alerts.db"


@dataclass
class Alert:
    id: int
    user_id: int
    symbol: str
    condition: str  # "above" | "below"
    price: float
    triggered: bool = False


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                symbol    TEXT NOT NULL,
                condition TEXT NOT NULL,
                price     REAL NOT NULL,
                triggered INTEGER DEFAULT 0
            )
        """)


def add_alert(user_id: int, symbol: str, condition: str, price: float) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO alerts (user_id, symbol, condition, price) VALUES (?, ?, ?, ?)",
            (user_id, symbol.upper(), condition, price)
        )
        return cur.lastrowid


def get_alerts(user_id: int) -> list[Alert]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, user_id, symbol, condition, price, triggered FROM alerts WHERE user_id=? AND triggered=0",
            (user_id,)
        ).fetchall()
    return [Alert(*r) for r in rows]


def get_all_active() -> list[Alert]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, user_id, symbol, condition, price, triggered FROM alerts WHERE triggered=0"
        ).fetchall()
    return [Alert(*r) for r in rows]


def remove_alert(user_id: int, alert_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM alerts WHERE id=? AND user_id=?",
            (alert_id, user_id)
        )
        return cur.rowcount > 0


def mark_triggered(alert_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE alerts SET triggered=1 WHERE id=?", (alert_id,))
