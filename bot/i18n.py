"""Translation strings for every bot-facing message.

`t(key, lang, **kwargs)` looks up `key` in `STRINGS`, picks the `lang` variant
(falling back to English if that key has no translation for `lang`, and to
the key itself if the key doesn't exist at all), and formats it with
`kwargs`. Handlers should never send a hardcoded string — always go through
`t()` so every reply respects the user's `/language` choice.
"""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # /start
    "welcome_greeting_named": {
        "en": "👋 Hi {name}! I'm your expense tracker.",
        "tr": "👋 Merhaba {name}! Ben senin harcama takip botunum.",
    },
    "welcome_greeting_anon": {
        "en": "👋 Hi! I'm your expense tracker.",
        "tr": "👋 Merhaba! Ben senin harcama takip botunum.",
    },
    "welcome_body": {
        "en": (
            "\n\nJust send me a message like:\n"
            "  50000 lunch\n"
            "  20 usd taxi to airport\n\n"
            "I'll default to {default_currency} if you skip the currency, and "
            "auto-detect a category unless you tag one with #category.\n\n"
            "Commands:\n"
            "/today — today's total\n"
            "/week — this week's total\n"
            "/month — this month's total, by category\n"
            "/undo — delete the last entry\n"
            "/export — download all expenses as CSV\n"
            "/help — full guide: every format, currency, and category keyword\n"
            "/language — change the bot's language\n\n"
            "🔒 Your expenses are private to you — no one else using this bot can see them."
        ),
        "tr": (
            "\n\nBenimle şöyle bir mesaj paylaşman yeterli:\n"
            "  50000 öğle yemeği\n"
            "  20 usd havalimanına taksi\n\n"
            "Para birimi belirtmezsen varsayılan olarak {default_currency} kullanırım, "
            "ve notunda bir #kategori etiketi olmadıkça kategoriyi kendim tahmin ederim.\n\n"
            "Komutlar:\n"
            "/today — bugünkü toplam\n"
            "/week — bu haftaki toplam\n"
            "/month — bu ayki toplam, kategoriye göre\n"
            "/undo — son kaydı sil\n"
            "/export — tüm harcamaları CSV olarak indir\n"
            "/help — tüm format, para birimi ve kategori anahtar kelimelerini gösteren rehber\n"
            "/language — botun dilini değiştir\n\n"
            "🔒 Harcamaların sadece sana özeldir — bu botu kullanan başka kimse onları göremez."
        ),
    },
    # /help
    "help_text": {
        "en": (
            "📖 Expense Bot — full guide\n\n"
            "LOGGING AN EXPENSE\n"
            "Just send a plain message — no command needed:\n"
            "  50000 lunch\n"
            "  20 usd taxi to airport\n"
            "  30 eur hotel deposit 20.07.2026\n"
            "  50000 lunch #food\n"
            "  20 usd taxi 05.01.2026 #transport\n\n"
            "Format: <amount> [currency] <note...> [#category] [date]\n"
            "  • Amount — first number in the message (50000, 50,000, 20.5, ...)\n"
            "  • Currency — optional 3-letter code right after the amount, "
            "defaults to {default_currency} if omitted\n"
            "  • #category — optional tag to override the auto-detected category\n"
            "  • Date — optional DD.MM.YYYY at the end, defaults to now\n"
            "    (#tag and date may appear in either order)\n"
            "  • Everything else in the message becomes the note\n\n"
            "SUPPORTED CURRENCIES\n  {currency_list}\n\n"
            "AUTO-DETECTED CATEGORIES\n"
            "(matched by keyword in your note, in English or Turkish — override "
            "anytime with #category)\n"
            "{category_lines}\n"
            "  {uncategorized_label}: anything that doesn't match a keyword above\n\n"
            "COMMANDS\n"
            "/today — today's total\n"
            "/week — this week's total\n"
            "/month — this month's total, broken down by category\n"
            "/undo — delete the last logged entry\n"
            "/export — download all your expenses as a CSV file\n"
            "/help — show this guide\n"
            "/language — change the bot's language"
        ),
        "tr": (
            "📖 Harcama Botu — tam rehber\n\n"
            "HARCAMA KAYDETME\n"
            "Sadece düz bir mesaj gönder — komuta gerek yok:\n"
            "  50000 öğle yemeği\n"
            "  20 usd havalimanına taksi\n"
            "  30 eur otel kaparosu 20.07.2026\n"
            "  50000 öğle yemeği #yemek\n"
            "  20 usd taksi 05.01.2026 #ulaşım\n\n"
            "Format: <tutar> [para birimi] <not...> [#kategori] [tarih]\n"
            "  • Tutar — mesajdaki ilk sayı (50000, 50.000, 20.5, ...)\n"
            "  • Para birimi — tutardan hemen sonra gelen isteğe bağlı 3 harfli "
            "kod, belirtilmezse {default_currency} kullanılır\n"
            "  • #kategori — otomatik algılanan kategoriyi geçersiz kılmak için "
            "isteğe bağlı etiket\n"
            "  • Tarih — sonda isteğe bağlı GG.AA.YYYY, belirtilmezse şu an kullanılır\n"
            "    (#etiket ve tarih herhangi bir sırada olabilir)\n"
            "  • Mesajdaki geri kalan her şey not olur\n\n"
            "DESTEKLENEN PARA BİRİMLERİ\n  {currency_list}\n\n"
            "OTOMATİK ALGILANAN KATEGORİLER\n"
            "(notundaki İngilizce veya Türkçe anahtar kelimeyle eşleştirilir — "
            "istediğin zaman #kategori ile geçersiz kılabilirsin)\n"
            "{category_lines}\n"
            "  {uncategorized_label}: yukarıdaki anahtar kelimelerden hiçbiriyle "
            "eşleşmeyen her şey\n\n"
            "KOMUTLAR\n"
            "/today — bugünkü toplam\n"
            "/week — bu haftaki toplam\n"
            "/month — bu ayki toplam, kategoriye göre\n"
            "/undo — son kaydı sil\n"
            "/export — tüm harcamaları CSV dosyası olarak indir\n"
            "/help — bu rehberi göster\n"
            "/language — botun dilini değiştir"
        ),
    },
    # logging an expense
    "expense_logged_with_note": {
        "en": "✅ Logged {amount} {currency} — {note} ({category})",
        "tr": "✅ Kaydedildi: {amount} {currency} — {note} ({category})",
    },
    "expense_logged_no_note": {
        "en": "✅ Logged {amount} {currency} ({category})",
        "tr": "✅ Kaydedildi: {amount} {currency} ({category})",
    },
    "no_amount_found": {
        "en": (
            "⚠️ I didn't see an amount in that message.\n\n"
            "Try something like:\n"
            "  50000 lunch\n"
            "  20 usd taxi to airport\n"
            "  50000 lunch 20.07.2026 #food\n\n"
            "Send /help to see everything I understand."
        ),
        "tr": (
            "⚠️ Mesajında bir tutar bulamadım.\n\n"
            "Şöyle bir şey dene:\n"
            "  50000 öğle yemeği\n"
            "  20 usd havalimanına taksi\n"
            "  50000 öğle yemeği 20.07.2026 #yemek\n\n"
            "Anladığım her şeyi görmek için /help yaz."
        ),
    },
    # /today, /week, /month
    "today_title": {"en": "📅 Today", "tr": "📅 Bugün"},
    "week_title": {"en": "🗓 This week", "tr": "🗓 Bu hafta"},
    "month_title": {"en": "📆 This month", "tr": "📆 Bu ay"},
    "no_expenses": {
        "en": "No expenses recorded.",
        "tr": "Henüz harcama kaydedilmedi.",
    },
    # /undo
    "undo_success_with_note": {
        "en": "🗑 Deleted {amount} {currency} — {note} ({category})",
        "tr": "🗑 Silindi: {amount} {currency} — {note} ({category})",
    },
    "undo_success_no_note": {
        "en": "🗑 Deleted {amount} {currency} ({category})",
        "tr": "🗑 Silindi: {amount} {currency} ({category})",
    },
    "undo_nothing": {
        "en": "Nothing to undo.",
        "tr": "Geri alınacak bir şey yok.",
    },
    # /export
    "export_ready": {
        "en": "📤 Here's your expense export.",
        "tr": "📤 Harcama dökümünüz hazır.",
    },
    "export_empty": {
        "en": "No expenses to export yet.",
        "tr": "Henüz dışa aktarılacak bir harcama yok.",
    },
    # access control
    "not_allowed": {
        "en": "🚫 Sorry, this bot is private and you're not on the allow-list.",
        "tr": "🚫 Üzgünüm, bu bot özeldir ve izin listesinde değilsin.",
    },
    # /language, /dil
    "choose_language": {
        "en": "Choose your language:",
        "tr": "Dilinizi seçin:",
    },
    "language_set_en": {
        "en": "✅ Language set to English.",
        "tr": "✅ Language set to English.",
    },
    "language_set_tr": {
        "en": "✅ Dil Türkçe olarak ayarlandı.",
        "tr": "✅ Dil Türkçe olarak ayarlandı.",
    },
}


def t(key: str, lang: str, **kwargs: object) -> str:
    """Look up a translated string and format it with kwargs.

    Falls back to English if `key` has no `lang` variant, and to the raw
    `key` if it isn't in `STRINGS` at all (so a typo'd key fails loudly-ish
    instead of crashing).
    """
    entry = STRINGS.get(key, {})
    template = entry.get(lang) or entry.get("en") or key
    return template.format(**kwargs)
