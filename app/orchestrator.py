import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Callable, Awaitable, List

from .browser import browser_manager
from .actions import spotify as spotify_actions
from .actions import whatsapp as whatsapp_actions
from . import db


@dataclass
class Action:
    name: str
    args: Dict[str, Any]
    priority: int = 50


class Orchestrator:
    def __init__(self) -> None:
        self._q: "asyncio.PriorityQueue[tuple[int, int, Action]]" = asyncio.PriorityQueue()
        self._seq = 0
        self._worker_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._worker_task:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker(), name="jarvis-worker")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except Exception:
                pass
            self._worker_task = None

    async def enqueue(self, action: Action) -> None:
        # Lower number = higher priority
        prio = int(action.priority)
        self._seq += 1
        await self._q.put((prio, self._seq, action))

    async def _worker(self) -> None:
        while self._running:
            prio, seq, action = await self._q.get()
            try:
                await self._dispatch(action)
                db.add_event(db_ts(), "action.ok", f"{action.name}")
            except Exception as e:
                db.add_event(db_ts(), "action.err", f"{action.name}: {e}")
            finally:
                self._q.task_done()

    async def _dispatch(self, action: Action) -> None:
        name = action.name
        args = action.args or {}

        if name == "spotify.play":
            sess = await browser_manager.spotify()
            await spotify_actions.play(sess.page, str(args.get("query", "")))
            return

        if name == "whatsapp.send":
            sess = await browser_manager.whatsapp()
            await whatsapp_actions.send_message(sess.page, str(args.get("contact", "")), str(args.get("message", "")))
            return

        if name == "reminder.add":
            text = str(args.get("text", ""))
            run_at = str(args.get("run_at", ""))
            db.add_reminder(text=text, run_at_iso=run_at)
            return

        raise RuntimeError(f"Acción no soportada: {name}")


def db_ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


orchestrator = Orchestrator()
