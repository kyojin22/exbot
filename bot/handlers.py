"""Telegram command + message handlers.

Kept thin: parsing lives in `parser.py`, category keywords in `categories.py`,
DB access in `db.py`. Handlers just glue Telegram <-> those modules together.
"""

from __future__ import annotations

import csv
import functools
import io
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Awaitable, Callable

from telegram import InputFile, Update
from telegram.ext import ContextTypes

from bot import categories, currencies, db
from bot.parser import parse_expense

PARSE_ERROR_TEXT = (
    "I didn't see an amount in that message.\n\n"
    "Try something like:\n"
    "  50000 lunch\n"
    "  20 usd taxi to airport\n"
    "  50000 lunch 20.07.2026 #food\n\n"
    "Send /help to see everything I understand."
)

START_TEXT = (
    "👋 Hi! Send me an expense like:\n"
    "  50000 lunch\n"
    "  20 usd taxi to airport\n\n"
    "I'll default to UZS if you don't give a currency, and auto-detect a "
    "category unless you tag one with #category.\n\n"
    "Send /help for the full guide, including every command and everything "
    "I understand in a message."
)

NOT_ALLOWED_TEXT = "🚫 Sorry, this bot is private and you're not on the allow-list."


def _build_help_text() -> str:
    """Compose the /help text dynamically from the currencies/categories modules
    so it never drifts out of sync with what the bot actually understands."""

    currency_list = ", ".join(
        sorted(currencies.SUPPORTED_CURRENCIES, key=lambda c: (c != currencies.DEFAULT_CURRENCY, c))
    )

    category_lines = "\n".join(
        f"  {category}: {', '.join(keywords)}"
        for category, keywords in categories.CATEGORY_KEYWORDS.items()
    )

    return (
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
        f"defaults to {currencies.DEFAULT_CURRENCY} if omitted\n"
        "  • #category — optional tag to override the auto-detected category\n"
        "  • Date — optional DD.MM.YYYY at the end, defaults to now\n"
        "    (#tag and date may appear in either order)\n"
        "  • Everything else in the message becomes the note\n\n"
        f"SUPPORTED CURRENCIES\n  {currency_list}\n\n"
        "AUTO-DETECTED CATEGORIES\n"
        "(matched by keyword in your note — override anytime with #category)\n"
        f"{category_lines}\n"
        f"  {categories.UNCATEGORIZED}: anything that doesn't match a keyword above\n\n"
        "COMMANDS\n"
        "/today — today's total\n"
        "/week — this week's total\n"
        "/month — this month's total, broken down by category\n"
        "/undo — delete the last logged entry\n"
        "/export — download all your expenses as a CSV file\n"
        "/help — show this guide"
    )


def _get_conn(context: ContextTypes.DEFAULT_TYPE):
    return db.get_connection(context.bot_data["db_path"])


def restricted(
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """Reject updates from chats not in ALLOWED_CHAT_IDS."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        allowed_chat_ids: set[int] = context.bot_data.get("allowed_chat_ids", set())
        chat_id = update.effective_chat.id if update.effective_chat else None
        if allowed_chat_ids and chat_id not in allowed_chat_ids:
            if update.message:
                await update.message.reply_text(NOT_ALLOWED_TEXT)
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


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT)


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_build_help_text())


@restricted
async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or not message.text:
        return

    parsed = parse_expense(message.text)
    if parsed is None:
        await message.reply_text(PARSE_ERROR_TEXT)
        return

    conn = _get_conn(context)
    try:
        db.insert_expense(
            conn,
            chat_id=update.effective_chat.id,
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
    if note_str:
        reply = f"✅ Logged {amount_str} {parsed.currency} — {note_str} ({parsed.category})"
    else:
        reply = f"✅ Logged {amount_str} {parsed.currency} ({parsed.category})"
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


def _format_summary(title: str, totals: dict[str, dict[str, float]], *, by_category: bool) -> str:
    if not totals:
        return f"{title}\nNo expenses recorded."

    lines = [title]
    for currency in sorted(totals):
        by_cat = totals[currency]
        grand_total = sum(by_cat.values())
        lines.append(f"\n{format_amount(grand_total)} {currency}")
        if by_category:
            for category, amount in sorted(by_cat.items(), key=lambda kv: -kv[1]):
                lines.append(f"  • {category}: {format_amount(amount)} {currency}")
    return "\n".join(lines)


@restricted
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_day(now))
    finally:
        conn.close()
    text = _format_summary("📅 Today", _summarize(expenses), by_category=False)
    await update.message.reply_text(text)


@restricted
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_week(now))
    finally:
        conn.close()
    text = _format_summary("🗓 This week", _summarize(expenses), by_category=False)
    await update.message.reply_text(text)


@restricted
async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    conn = _get_conn(context)
    try:
        expenses = db.get_expenses_since(conn, chat_id=update.effective_chat.id, since=_start_of_month(now))
    finally:
        conn.close()
    text = _format_summary("📆 This month", _summarize(expenses), by_category=True)
    await update.message.reply_text(text)


@restricted
async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = _get_conn(context)
    try:
        last = db.get_last_expense(conn, chat_id=update.effective_chat.id)
        if last is None:
            await update.message.reply_text("Nothing to undo.")
            return
        db.delete_expense(conn, expense_id=last.id)
    finally:
        conn.close()

    amount_str = format_amount(last.amount)
    await update.message.reply_text(
        f"🗑 Deleted {amount_str} {last.currency} — {last.note or last.category} ({last.category})"
    )


@restricted
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = _get_conn(context)
    try:
        expenses = db.get_all_expenses(conn, chat_id=update.effective_chat.id)
    finally:
        conn.close()

    if not expenses:
        await update.message.reply_text("No expenses to export yet.")
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
    await update.message.reply_document(document=InputFile(data, filename="expenses.csv"))
