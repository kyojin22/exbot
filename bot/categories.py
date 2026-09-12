"""Keyword -> category mapping used for auto-detection.

Categories are stored as canonical, language-independent keys (`"food"`,
`"transport"`, ...) rather than display strings, so the same category can be
rendered in whichever language the user has chosen (see `bot/i18n.py`) without
touching the data. `CATEGORY_DISPLAY` maps each canonical key to its per-
language display name.

`detect_category` runs a simple case-insensitive substring match against the
note text and returns the first matching canonical key, or `UNCATEGORIZED` if
nothing matches. It intentionally does *not* depend on the user's chosen
display language — a message can be typed in Turkish even if the user's
`/language` is set to English (and vice versa), so both language's keyword
lists are always checked together.
"""

from __future__ import annotations

UNCATEGORIZED = "uncategorized"

# Canonical key -> display name per language.
CATEGORY_DISPLAY: dict[str, dict[str, str]] = {
    "food": {"en": "Food", "tr": "Yemek"},
    "transport": {"en": "Transport", "tr": "Ulaşım"},
    "bills": {"en": "Bills", "tr": "Faturalar"},
    "health": {"en": "Health", "tr": "Sağlık"},
    "entertainment": {"en": "Entertainment", "tr": "Eğlence"},
    "shopping": {"en": "Shopping", "tr": "Alışveriş"},
    UNCATEGORIZED: {"en": "Uncategorized", "tr": "Kategorisiz"},
}

# Order matters: first matching category wins. Keep keywords lowercase.
# Each list mixes English and Turkish keywords — matching doesn't depend on
# the user's display language, so both are always checked together.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "lunch", "dinner", "breakfast", "coffee", "food", "restaurant",
        "cafe", "grocery", "groceries", "snack", "pizza", "burger",
        "öğle yemeği", "akşam yemeği", "kahvaltı", "kahve", "yemek",
        "restoran", "kafe", "market", "atıştırmalık",
    ],
    "transport": [
        "taxi", "uber", "bus", "metro", "train", "gas", "fuel", "parking",
        "flight", "airport",
        "taksi", "otobüs", "tren", "benzin", "yakıt", "park", "uçak",
        "havalimanı", "ulaşım",
    ],
    "bills": [
        "rent", "utilities", "electricity", "water bill", "internet",
        "hotel",
        "kira", "fatura", "elektrik", "su faturası", "internet", "otel",
    ],
    "health": [
        "pharmacy", "doctor", "hospital", "medicine", "clinic",
        "eczane", "doktor", "hastane", "ilaç", "klinik",
    ],
    "entertainment": [
        "movie", "cinema", "netflix", "spotify", "game", "concert",
        "film", "sinema", "oyun", "konser",
    ],
    "shopping": [
        "clothes", "shoes", "shopping", "mall",
        "kıyafet", "ayakkabı", "alışveriş", "avm",
    ],
}


def detect_category(note: str) -> str:
    """Detect a canonical category key from free text via keyword matching.

    Case-insensitive substring match against `note`, across every language's
    keywords at once. Returns the first matching category in
    `CATEGORY_KEYWORDS` order, or `UNCATEGORIZED`.
    """
    lowered = note.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return category
    return UNCATEGORIZED


def get_category_display(category_key: str, lang: str) -> str:
    """Translate a canonical category key (or a free-form #tag) for display.

    Falls back to English, then to a capitalized version of the raw key
    itself — so a custom `#tag` that isn't one of the known categories still
    displays reasonably instead of raising.
    """
    entry = CATEGORY_DISPLAY.get(category_key)
    if entry is None:
        return category_key.capitalize()
    return entry.get(lang) or entry.get("en") or category_key.capitalize()
