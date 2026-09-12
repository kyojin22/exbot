"""Telegram command + message handlers.

Kept thin: parsing lives in `parser.py`, category keywords in `categories.py`,
translated strings in `i18n.py`, DB access in `db.py`. Handlers just glue
Telegram <-> those modules together.

Every user-facing reply goes through `i18n.t(key, lang, ...)`, where `lang`
is the chat's stored preference (`db.get_user_language`) — never a hardcoded
string — so `/language` fully controls what a chat sees.
"""

from __future__ import annotations

import csv
import functools
import io
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Awaitable, Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import ContextTypes

from bot import categories, currencies, db
from bot.i18n import t
from bot.parser import parse_expense

LANGUAGE_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang:tr"),
        ]
    ]
)


def _get_conn(context: ContextTypes.DEFAULT_TYPE):
    return db.get_connection(context.bot_data["db_path"])


def _get_lang(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> str:
    conn = _get_conn(context)
    try:
        return db.get_user_language(conn, chat_id)
    finally:
        conn.close()


def restricted(
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """Reject updates from chats not in ALLOWED_CHAT_IDS.

    Handles both plain messages and callback queries (inline button taps),
    since the /language picker uses the latter.
    """

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        allowed_chat_ids: set[int] = context.bot_data.get("allowed_chat_ids", set())
        chat_id = update.effective_chat.id if update.effective_chat else None
        if allowed_chat_ids and chat_id not in allowed_chat_ids:
            lang = _get_lang(context, chat_id) if chat_id is not None else "en"
            text = t("not_allowed", lang)
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.reply_text(text)
            elif update.message:
                await update.message.reply_text(text)
            return
        await handler(update, context)

    return wrapper


def format_amount(amount: float) -> str:
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def _display_note(note: str) -> str:
    if not note:
        return ""
    return note[0].upper() + note[1:]


def _build_welcome_text(first_name: str | None, lang: str) -> str:
    if first_name:
        greeting = t("welcome_greeting_named", lang, name=first_name)
    else:
        greeting = t("welcome_greeting_anon", lang)
    body = t("welcome_body", lang, default_currency=currencies.DEFAULT_CURRENCY)
    return greeting + body


def _build_help_text(lang: str) -> str:
    """Compose the /help text dynamically from the currencies/categories modules
    so it never drifts out of sync with what the bot actually understands."""

    currency_list = ", ".join(
        sorted(currencies.SUPPORTED_CURRENCIES, key=lambda c: (c != currencies.DEFAULT_CURRENCY, c))
    )

    category_lines = "\n".join(
        f"  {categories.get_category_display(category, lang)}: {', '.join(keywords)}"
        for category, keywords in categories.CATEGORY_KEYWORDS.items()
    )

    return t(
        "help_text",
        lang,
        default_currency=currencies.DEFAULT_CURRENCY,
        currency_list=currency_list,
        category_lines=category_lines,
        uncategorized_label=categories.get_category_display(categories.UNCATEGORIZED, lang),
    )


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conn = _get_conn(context)
    try:
        is_first_time = not db.has_language_preference(conn, chat_id)
        lang = db.get_user_language(conn, chat_id)
    finally:
        conn.close()

    if is_first_time:
        # Brand-new chat: let them pick a language before anything else,
        # rather than assuming they read English.
        await update.message.reply_text(t("choose_language", lang), reply_markup=LANGUAGE_KEYBOARD)
        return

    first_name = update.effective_user.first_name if update.effective_user else None
    await update.message.reply_text(_build_welcome_text(first_name, lang))


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _get_lang(context, update.effective_chat.id)
    await update.message.reply_text(_build_help_text(lang))


@restricted
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _get_lang(context, update.effective_chat.id)
    await update.message.reply_text(t("choose_language", lang), reply_markup=LANGUAGE_KEYBOARD)


@restricted
async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for the inline English/Türkçe buttons from /language, /dil, or /start."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(":", 1)[1] if query.data else ""
    if lang_code not in ("en", "tr"):
        return

    chat_id = update.effective_chat.id
    conn = _get_conn(context)
    try:
        is_first_time = not db.has_language_preference(conn, chat_id)
        db.set_user_language(conn, chat_id, lang_code)
    finally:
        conn.close()

    confirmation_key = "language_set_en" if lang_code == "en" else "language_set_tr"
    await query.edit_message_text(t(confirmation_key, lang_code))

    if is_first_time:
        # This was the auto-shown picker on a brand-new chat's first /start —
        # follow the confirmation with the usual welcome/instructions.
        first_name = update.effective_user.first_name if update.effective_user else None
        await query.message.reply_text(_build_welcome_text(first_name, lang_code))


@restricted
async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or not message.text:
        return

    chat_id = update.effective_chat.id
    lang = _get_lang(context, chat_id)

    parsed = parse_expense(message.text)
    if parsed is None:
        await message.reply_text(t("no_amount_found", lang))
        return

    conn = _get_conn(context)
    try:
        db.insert_expense(
            conn,
            chat_id=chat_id,
            amount=parsed.amount,
            currency=parsed.currency,
            category=parsed.category,
            note=parsed.note,
            raw_message=parsed.raw_message,
            created_at=parsed.expense_date,
        )
    finally:
        conn.close()

    amount_str = format_amount(parsed.amount)
    note_str = _display_note(parsed.note)
    category_display = categories.get_category_display(parsed.category, lang)
    if note_str:
        reply = t(
            "expense_logged_with_note",
            lang,
            amount=amount_str,
            currency=parsed.currency,
            note=note_str,
            category=category_display,
        )
    else:
        reply = t(
            "expense_logged_no_note",
            lang,
            amount=amount_str,
            currency=parsed.currency,
            category=category_display,
        )
    await message.reply_text(reply)


def _start_of_day(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(now: datetime) -> datetime:
    start_of_day = _start_of_day(now)
    return start_of_day - timedelta(days=start_of_day.weekday())  # Monday


def _start_of_month(now: datetime) -> datetime:
    return _start_of_day(now).replace(day=1)


def _summarize(expenses: list[db.Expense]) -> dict[str, dict[str, float]]:
    """currency -> {category -> total}"""
    totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for exp in expenses:
        totals[exp.currency][exp.category] += exp.amount
    return totals


def _format_summary(
    title: str, totals: dict[str, dict[str, float]], *, lang: str, by_category: bool
) -> str:
    if not totals:
        return f"{title}\n{t('no_expenses', lang)}"

    lines = [title]
    for currency in sorted(totals):
        by_cat = totals[currency]
        grand_total = sum(by_cat.values())
        lines.append(f"\n{format_amount(grand_total)} {currency}")
        if by_category:
            for category, amount in sorted(by_cat.items(), key=lambda kv: -kv[1]):
                category_display = categories.get_category_display(category, lang)
                lines.append(f"  • {category_display}: {format_amount(amount)} {currency}")
    return "\n".join(lines)


@restricted
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    lang = _get_lang(context, update.effective_chat.id)
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_day(now))
    finally:
        conn.close()
    text = _format_summary(t("today_title", lang), _summarize(expenses), lang=lang, by_category=False)
    await update.message.reply_text(text)


@restricted
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    lang = _get_lang(context, update.effective_chat.id)
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_week(now))
    finally:
        conn.close()
    text = _format_summary(t("week_title", lang), _summarize(expenses), lang=lang, by_category=False)
    await update.message.reply_text(text)


@restricted
async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    lang = _get_lang(context, update.effective_chat.id)
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_month(now))
    finally:
        conn.close()
    text = _format_summary(t("month_title", lang), _summarize(expenses), lang=lang, by_category=True)
    await update.message.reply_text(text)


@restricted
async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _get_lang(context, update.effective_chat.id)
    conn = _get_conn(context)
    try:
        last = db.get_last_expense(conn, chat_id=update.effective_chat.id)
        if last is None:
            await update.message.reply_text(t("undo_nothing", lang))
            return
        db.delete_expense(conn, expense_id=last.id)
    finally:
        conn.close()

    amount_str = format_amount(last.amount)
    category_display = categories.get_category_display(last.category, lang)
    if last.note:
        reply = t(
            "undo_success_with_note",
            lang,
            amount=amount_str,
            currency=last.currency,
            note=last.note,
            category=category_display,
        )
    else:
        reply = t(
            "undo_success_no_note",
            lang,
            amount=amount_str,
            currency=last.currency,
            category=category_display,
        )
    await update.message.reply_text(reply)


@restricted
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _get_lang(context, update.effective_chat.id)
    conn = _get_conn(context)
    try:
        expenses = db.get_all_expenses(conn, chat_id=update.effective_chat.id)
    finally:
        conn.close()

    if not expenses:
        await update.message.reply_text(t("export_empty", lang))
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "amount", "currency", "category", "note", "raw_message", "created_at"])
    for exp in expenses:
        writer.writerow(
            [exp.id, exp.amount, exp.currency, exp.category, exp.note, exp.raw_message, exp.created_at]
        )

    data = io.BytesIO(buffer.getvalue().encode("utf-8"))
    data.name = "expenses.csv"
    await update.message.reply_document(
        document=InputFile(data, filename="expenses.csv"),
        caption=t("export_ready", lang),
    )
