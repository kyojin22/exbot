"""Keyword -> category mapping used for auto-detection.

`detect_category` runs a simple case-insensitive substring/word match against
the note text and returns the first matching category, or "Uncategorized" if
nothing matches.
"""

from __future__ import annotations

UNCATEGORIZED = "Uncategorized"

# Order matters: first matching category wins. Keep keywords lowercase.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food": [
        "lunch", "dinner", "breakfast", "coffee", "food", "restaurant",
        "cafe", "grocery", "groceries", "snack", "pizza", "burger",
    ],
    "Transport": [
        "taxi", "uber", "bus", "metro", "train", "gas", "fuel", "parking",
        "flight", "airport",
    ],
    "Housing": [
        "rent", "utilities", "electricity", "water bill", "internet",
        "hotel",
    ],
    "Health": [
        "pharmacy", "doctor", "hospital", "medicine", "clinic",
    ],
    "Entertainment": [
        "movie", "cinema", "netflix", "spotify", "game", "concert",
    ],
    "Shopping": [
        "clothes", "shoes", "shopping", "mall",
    ],
}


def detect_category(note: str) -> str:
    """Detect a category from free text via keyword matching.

    Case-insensitive substring match against `note`. Returns the first
    matching category in `CATEGORY_KEYWORDS` order, or "Uncategorized".
    """
    lowered = note.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return category
    return UNCATEGORIZED
