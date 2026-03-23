"""General-purpose helper utilities."""

import re
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)
