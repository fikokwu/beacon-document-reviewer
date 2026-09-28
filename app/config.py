"""Runtime configuration from environment variables (.env locally, Cloud Run env in prod)."""

import os

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
# Form detection is simple; a Flash model does it 8/8 correctly and faster (ADR-016).
GEMINI_CLASSIFY_MODEL = os.getenv("GEMINI_CLASSIFY_MODEL", "gemini-3.5-flash").strip()
# Used automatically if the main model is rate-limited (429) — separate quota (ADR-018).
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash").strip()
GEMINI_TIMEOUT_S = float(os.getenv("GEMINI_TIMEOUT_S", "60"))
# Ask the model for per-cell bounding boxes (slower; only needed for highlighting).
GEMINI_REQUEST_BOXES = _flag("GEMINI_REQUEST_BOXES", False)
# Optional thinking level for models that support it ("low" is faster). Empty = model default.
GEMINI_THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "").strip() or None

# QS-F-049 dates: False accepts / - . as separators; True accepts only /.  (ADR-004)
STRICT_DATE_SEPARATOR = _flag("STRICT_DATE_SEPARATOR", False)
