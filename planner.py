import json
import re
from typing import Any, Dict, List

from huggingface_hub import InferenceClient

from . import settings


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    m = _JSON_RE.search(text)
    if not m:
        raise ValueError("No JSON found in model output")
    return json.loads(m.group(0))


def rules_plan(user_text: str) -> Dict[str, Any]:
    t = user_text.lower()
    actions: List[Dict[str, Any]] = []
    speak = ""

    # Spotify
    if any(w in t for w in ["pon ", "reproduce", "play ", "ponme"]):
        # naive: remove common prefixes
        q = user_text
        for p in ["pon ", "ponme ", "reproduce ", "play "]:
            if t.startswith(p):
                q = user_text[len(p):].strip()
                break
        actions.append({"name": "spotify.play", "args": {"query": q}, "priority": 50})
        speak = f"Reproduciendo {q}."

    # WhatsApp: "manda a <contacto> <mensaje>"
    if t.startswith("manda a ") or t.startswith("envia a ") or t.startswith("envía a "):
        rest = user_text.split(" ", 2)
        if len(rest) >= 3:
            # rest[0]=manda, rest[1]=a, rest[2]=<contacto> <mensaje>
            tail = rest[2]
            parts = tail.split(" ", 1)
            contact = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else ""
            actions.append({"name": "whatsapp.send", "args": {"contact": contact, "message": message}, "priority": 60})
            speak = "Mensaje en camino."

    # Reminder: "recuérdame <texto> a las <hora>" (muy básico)
    if "recuérdame" in t or "recuerdame" in t:
        speak = speak or "Listo."

    return {"response": speak, "actions": actions, "constraints": {}}


def llm_plan(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    if settings.PLANNER_MODE == "rules":
        user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_text = m.get("content", "")
                break
        return rules_plan(user_text)

    if not settings.HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not set. Set PLANNER_MODE=rules or configure HF_TOKEN.")

    client = InferenceClient(provider=settings.HF_PROVIDER, api_key=settings.HF_TOKEN)
    resp = client.chat.completions.create(
        model=settings.HF_MODEL,
        messages=messages,
        max_tokens=settings.HF_MAX_TOKENS,
        temperature=settings.HF_TEMPERATURE,
    )
    content = resp.choices[0].message.content
    plan = _extract_json(content)

    plan.setdefault("response", "")
    plan.setdefault("actions", [])
    plan.setdefault("constraints", {})
    return plan
