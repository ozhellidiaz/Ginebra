import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from . import settings


def db_path() -> str:
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    return os.path.join(settings.DATA_DIR, "jarvis.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS kv (
          key TEXT PRIMARY KEY,
          value TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          text TEXT NOT NULL,
          run_at TEXT NOT NULL,
          fired INTEGER NOT NULL DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          label TEXT,
          run_at TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          kind TEXT NOT NULL,
          message TEXT
        )
        """)
        conn.commit()


def kv_get(key: str) -> Optional[str]:
    with db() as conn:
        row = conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return None if row is None else row[0]


def kv_set(key: str, value: str) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


def add_event(ts_iso: str, kind: str, message: str = "") -> None:
    with db() as conn:
        conn.execute("INSERT INTO events(ts,kind,message) VALUES(?,?,?)", (ts_iso, kind, message))
        conn.commit()


def list_events(limit: int = 50):
    with db() as conn:
        return conn.execute("SELECT ts,kind,message FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def add_reminder(text: str, run_at_iso: str) -> None:
    with db() as conn:
        conn.execute("INSERT INTO reminders(text,run_at,fired) VALUES(?,?,0)", (text, run_at_iso))
        conn.commit()


def due_reminders(now_iso: str):
    with db() as conn:
        return conn.execute(
            "SELECT id,text,run_at FROM reminders WHERE fired=0 AND run_at<=? ORDER BY run_at ASC",
            (now_iso,),
        ).fetchall()


def mark_reminder_fired(reminder_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE reminders SET fired=1 WHERE id=?", (reminder_id,))
        conn.commit()


def add_alarm(label: str, run_at_iso: str) -> None:
    with db() as conn:
        conn.execute("INSERT INTO alarms(label,run_at,active) VALUES(?,?,1)", (label, run_at_iso))
        conn.commit()


def due_alarms(now_iso: str):
    with db() as conn:
        return conn.execute(
            "SELECT id,label,run_at FROM alarms WHERE active=1 AND run_at<=? ORDER BY run_at ASC",
            (now_iso,),
        ).fetchall()


def deactivate_alarm(alarm_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE alarms SET active=0 WHERE id=?", (alarm_id,))
        conn.commit()
