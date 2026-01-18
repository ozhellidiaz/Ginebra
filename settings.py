import os


def env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return default if v is None else v


# Fly sets PORT; default 8080 for fly.toml internal_port.
PORT: int = int(env("PORT", "8080"))

# Persistent data root (Fly Volume mounted here)
DATA_DIR: str = env("DATA_DIR", "/data")

# Optional bearer token for API endpoints (recommended)
API_BEARER_TOKEN: str = env("API_BEARER_TOKEN", "").strip()

# Planner mode: "llm" (default) or "rules"
PLANNER_MODE: str = env("PLANNER_MODE", "llm").strip().lower()

# HuggingFace Hub InferenceClient (provider-backed) config
HF_TOKEN: str = env("HF_TOKEN", "").strip()
HF_PROVIDER: str = env("HF_PROVIDER", "fireworks-ai").strip()  # e.g. "fireworks-ai"
HF_MODEL: str = env("HF_MODEL", "openai/gpt-oss-120b").strip()
HF_MAX_TOKENS: int = int(env("HF_MAX_TOKENS", "900"))
HF_TEMPERATURE: float = float(env("HF_TEMPERATURE", "0.2"))

# Playwright
PW_HEADLESS: bool = env("PW_HEADLESS", "1").strip() not in ("0", "false", "False")

# OpenWeather (optional for wakeup)
OPENWEATHER_API_KEY: str = env("OPENWEATHER_API_KEY", "").strip()
