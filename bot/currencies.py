"""Allow-list of supported 3-letter currency codes.

Kept small and explicit (rather than full ISO 4217) to avoid false positives
where an ordinary word in a note accidentally looks like a currency code.
"""

from __future__ import annotations

import os

DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "UZS").upper()


def _load_supported_currencies() -> frozenset[str]:
    raw = os.getenv("SUPPORTED_CURRENCIES", "UZS,USD,EUR,RUB")
    codes = {code.strip().upper() for code in raw.split(",") if code.strip()}
    codes.add(DEFAULT_CURRENCY)
    return frozenset(codes)


SUPPORTED_CURRENCIES: frozenset[str] = _load_supported_currencies()


def is_supported_currency(token: str) -> bool:
    """Return True if `token` matches a known 3-letter currency code (case-insensitive)."""
    return token.upper() in SUPPORTED_CURRENCIES
