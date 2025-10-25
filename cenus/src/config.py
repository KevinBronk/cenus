# src/config.py
import os
from dotenv import load_dotenv

# load from .env in local dev; in Replit/GitHub we use Secrets
load_dotenv()

def _need(name: str, fallback: str | None = None) -> str:
    val = os.getenv(name)
    if not val and fallback:
        val = os.getenv(fallback)
    if not val:
        raise RuntimeError(f"Missing env var: {name}" + (f" (or {fallback})" if fallback else ""))
    return val

def mask(token: str, keep: int = 6) -> str:
    if not token: return ""
    if len(token) <= keep: return "*" * len(token)
    return token[:keep] + "…" + "*" * (len(token) - keep)

META_API_VERSION = os.getenv("META_API_VERSION", "v20.0")

# Accept either FB_ACCESS_TOKEN or fallback FB_TOKEN
FB_ACCESS_TOKEN    = _need("FB_ACCESS_TOKEN", fallback="FB_TOKEN")
FB_APP_ID          = _need("FB_APP_ID")
FB_APP_SECRET      = _need("FB_APP_SECRET")
NOTION_TOKEN       = _need("NOTION_TOKEN")
SLACK_WEBHOOK_URL  = _need("SLACK_WEBHOOK_URL")
NOTION_ROOT_PAGE_ID = _need("NOTION_ROOT_PAGE_ID")
