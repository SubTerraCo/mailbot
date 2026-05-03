from __future__ import annotations

import re
from email.utils import parseaddr


def extract_email_and_name(from_header: str | None) -> tuple[str | None, str | None]:
    """
    Parse RFC From header; return (email_lower, display_name_or_none).
    """
    if not from_header:
        return None, None
    name, addr = parseaddr(from_header)
    addr = addr.strip().lower() if addr else None
    name = name.strip() if name else None
    return addr, name or None


def domain_from_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[-1].lower()


_ANGRY_ANGLE = re.compile(r"<([^>]+)>")


def normalize_from_header(raw: str | None) -> str | None:
    """Best-effort strip angle brackets from visible From."""
    if not raw:
        return None
    m = _ANGRY_ANGLE.search(raw)
    if m:
        return m.group(1).strip().lower()
    email, _ = extract_email_and_name(raw)
    return email
