import os
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import settings, db
from .planner import llm_plan
from .orchestrator import orchestrator, Action
from .browser import browser_manager
from .background import reminder_loop, alarm_loop


def _auth_or_raise(authorization: Optional[str]) -> None:
    if not settings.API_BEARER_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != settings.API_BEARER_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


app = FastAPI(title="Jarvis Web")

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

_stop_event = asyncio.Event()
_bg_tasks: list[asyncio.Task] = []


@app.on_event("startup")
async def _startup() -> None:
    db.init_db()
    await orchestrator.start()

    _stop_event.clear()
    _bg_tasks.clear()
    _bg_tasks.append(asyncio.create_task(reminder_loop(_stop_event), name="reminders"))
    _bg_tasks.append(asyncio.create_task(alarm_loop(_stop_event), name="alarms"))


@app.on_event("shutdown")
async def _shutdown() -> None:
    _stop_event.set()
    for t in _bg_tasks:
        t.cancel()
    await orchestrator.stop()
    await browser_manager.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/message")
async def api_message(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)):
    _auth_or_raise(authorization)

    text = str(payload.get("text", "")).strip()
    if not text:
        return JSONResponse({"response": "", "plan": {"actions": []}, "events": []})

    system = (
        'Eres un orquestador. Devuelve SOLO JSON valido con esta forma: '
        '{"response": string, "actions": [{"name": string, "args": object, "priority": int}], "constraints": object}. '
        'No incluyas texto fuera del JSON.'
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    plan = llm_plan(messages)

    # Enqueue actions
    actions = plan.get("actions", []) or []
    for a in actions:
        try:
            name = str(a.get("name"))
            args = a.get("args") or {}
            prio = int(a.get("priority", 50))
            await orchestrator.enqueue(Action(name=name, args=args, priority=prio))
        except Exception as e:
            db.add_event(db_ts(), "plan.action.err", str(e))

    # Log the assistant response
    if plan.get("response"):
        db.add_event(db_ts(), "assistant", str(plan.get("response")))

    events = [dict(r) for r in db.list_events(30)]
    return JSONResponse({"response": plan.get("response", ""), "plan": plan, "events": events})


@app.get("/api/events")
async def api_events(limit: int = 50, authorization: Optional[str] = Header(default=None)):
    _auth_or_raise(authorization)
    return JSONResponse({"events": [dict(r) for r in db.list_events(limit)]})


@app.get("/auth/whatsapp.png")
async def whatsapp_png(authorization: Optional[str] = Header(default=None)):
    _auth_or_raise(authorization)
    img = await browser_manager.screenshot_whatsapp()
    return Response(content=img, media_type="image/png")


@app.get("/auth/spotify.png")
async def spotify_png(authorization: Optional[str] = Header(default=None)):
    _auth_or_raise(authorization)
    img = await browser_manager.screenshot_spotify()
    return Response(content=img, media_type="image/png")


@app.get("/health")
async def health():
    # Health check endpoint
    return {"ok": True}


def db_ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
