"""Pure expense-message parsing logic.

No Telegram API calls here — these are plain functions that take a string
(and optionally a reference "now") and return a `ParsedExpense`, so they're
easy to unit test in isolation. See CLAUDE.md section 6 for the full spec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from bot.categories import detect_category
from bot.currencies import DEFAULT_CURRENCY, is_supported_currency

# A token that is purely a number, optionally with thousands separators
# and/or a decimal part: "50000", "50,000", "20.5"
_NUMBER_TOKEN_RE = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$|^\d+(?:\.\d+)?$")

# DD.MM.YYYY
_DATE_TOKEN_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")

# #category tag — word characters only (letters/digits/underscore, unicode-aware)
_TAG_TOKEN_RE = re.compile(r"^#(\w+)$", re.UNICODE)


@dataclass
class ParsedExpense:
    amount: float
    currency: str
    category: str
    note: str
    expense_date: datetime
    raw_message: str


def parse_expense(text: str, now: datetime | None = None) -> ParsedExpense | None:
    """Parse a free-text expense message.

    Returns `None` if no amount could be found in `text` — callers should
    treat that as "not an expense message" and show a help hint instead of
    logging anything.
    """
    if now is None:
        now = datetime.now()

    tokens = text.strip().split()
    if not tokens:
        return None

    amount, amount_idx = _extract_amount(tokens)
    if amount is None:
        return None

    # Remove the amount token; everything else stays in original order.
    remaining = tokens[:amount_idx] + tokens[amount_idx + 1 :]

    currency, remaining = _extract_currency(remaining, currency_token_idx=amount_idx)
    expense_date, category_tag, remaining = _extract_trailing_date_and_tag(remaining, now)

    note = " ".join(remaining).strip()
    category = category_tag.capitalize() if category_tag else detect_category(note)

    return ParsedExpense(
        amount=amount,
        currency=currency,
        category=category,
        note=note,
        expense_date=expense_date,
        raw_message=text,
    )


def _extract_amount(tokens: list[str]) -> tuple[float | None, int]:
    """Find the first token that looks like a plain number."""
    for i, tok in enumerate(tokens):
        if _NUMBER_TOKEN_RE.match(tok):
            return float(tok.replace(",", "")), i
    return None, -1


def _extract_currency(remaining: list[str], currency_token_idx: int) -> tuple[str, list[str]]:
    """Consume the token right after the amount if it's a known currency code.

    `currency_token_idx` is the amount's original index, which — since the
    amount token has already been removed — is exactly where the following
    token now sits in `remaining` (if there is one).
    """
    if currency_token_idx < len(remaining) and is_supported_currency(remaining[currency_token_idx]):
        currency = remaining[currency_token_idx].upper()
        remaining = remaining[:currency_token_idx] + remaining[currency_token_idx + 1 :]
        return currency, remaining
    return DEFAULT_CURRENCY, remaining


def _extract_trailing_date_and_tag(
    remaining: list[str], now: datetime
) -> tuple[datetime, str | None, list[str]]:
    """Strip a trailing date and/or #tag from the end of the message.

    They may appear in either order, so repeatedly check the last token
    until it matches neither pattern.
    """
    remaining = list(remaining)
    expense_date = now
    category_tag: str | None = None

    while remaining:
        last = remaining[-1]

        date_match = _DATE_TOKEN_RE.match(last)
        if date_match:
            day, month, year = (int(g) for g in date_match.groups())
            try:
                expense_date = datetime(year, month, day)
            except ValueError:
                break  # looks like a date but isn't valid — leave it in the note
            remaining.pop()
            continue

        tag_match = _TAG_TOKEN_RE.match(last)
        if tag_match:
            category_tag = tag_match.group(1)
            remaining.pop()
            continue

        break

    return expense_date, category_tag, remaining
