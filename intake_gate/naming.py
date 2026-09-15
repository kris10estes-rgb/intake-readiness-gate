"""Naming-convention builder.

One clean filename every time: LOCATION-Sxx-TYPE-YYYYMMDD. The rule is
small on purpose. It exists to remove a whole class of manual naming errors,
not to be clever.
"""

from __future__ import annotations

import re
from datetime import date

CONTENT_TYPES: tuple[str, ...] = ("PROMO", "MENU", "EVERGREEN", "CAMPAIGN", "WAYFINDING")
_PATTERN = re.compile(r"^[A-Z0-9]+-S\d{2,}-(" + "|".join(CONTENT_TYPES) + r")-\d{8}$")


def build_name(location: str, screen: int, content_type: str, live_date: date) -> str:
    loc = re.sub(r"[^A-Z0-9]", "", (location or "").upper())
    if not loc:
        raise ValueError("location code is required")
    if not isinstance(screen, int) or isinstance(screen, bool) or screen < 1:
        raise ValueError("screen number must be a positive integer")
    ctype = (content_type or "").upper()
    if ctype not in CONTENT_TYPES:
        raise ValueError(f"content type must be one of {', '.join(CONTENT_TYPES)}")
    return f"{loc}-S{screen:02d}-{ctype}-{live_date:%Y%m%d}"


def is_valid_name(name: str) -> bool:
    return bool(_PATTERN.match(name))
