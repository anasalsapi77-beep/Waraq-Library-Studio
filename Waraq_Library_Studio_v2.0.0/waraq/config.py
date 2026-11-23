"""Application configuration and filesystem paths."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_ROOT = PROJECT_ROOT / "static"
DATA_ROOT = PROJECT_ROOT / "data"
DB_PATH = Path(os.environ.get("LIBRARY_DB", DATA_ROOT / "library.db")).expanduser()
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
SESSION_TTL_SECONDS = 12 * 60 * 60
MAX_FORM_BYTES = 64 * 1024
DEMO_MODE = os.environ.get("WARAQ_DEMO_MODE", "1").strip().lower() not in {"0", "false", "no", "off"}
COOKIE_SECURE = os.environ.get("WARAQ_COOKIE_SECURE", "0").strip().lower() in {"1", "true", "yes", "on"}
