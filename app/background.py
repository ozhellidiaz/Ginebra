import asyncio
from datetime import datetime, timezone

from . import db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def reminder_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            for row in db.due_reminders(now_iso()):
                db.mark_reminder_fired(int(row["id"]))
                db.add_event(now_iso(), "reminder", row["text"])
        except Exception as e:
            db.add_event(now_iso(), "reminder.err", str(e))
        await asyncio.sleep(5)


async def alarm_loop(stop_event: asyncio.Event) -> None:
    # For now alarms just emit an event; you can extend to run wakeup routine.
    while not stop_event.is_set():
        try:
            for row in db.due_alarms(now_iso()):
                db.deactivate_alarm(int(row["id"]))
                db.add_event(now_iso(), "alarm", row.get("label") or "alarm")
        except Exception as e:
            db.add_event(now_iso(), "alarm.err", str(e))
        await asyncio.sleep(5)
