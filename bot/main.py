"""Entry point: loads config, initializes the DB, and starts polling."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot import db, handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _parse_allowed_chat_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            logger.warning("Ignoring invalid chat id in ALLOWED_CHAT_IDS: %r", part)
    return ids


def main() -> None:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise SystemExit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

    db_path = os.getenv("DB_PATH", "./data/expenses.db")
    allowed_chat_ids = _parse_allowed_chat_ids(os.getenv("ALLOWED_CHAT_IDS", ""))
    if not allowed_chat_ids:
        logger.warning(
            "ALLOWED_CHAT_IDS is empty — the bot will respond to *anyone*. "
            "Set it in .env to restrict access."
        )

    db.init_db(db_path)

    application = Application.builder().token(bot_token).build()
    application.bot_data["db_path"] = db_path
    application.bot_data["allowed_chat_ids"] = allowed_chat_ids

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("today", handlers.today))
    application.add_handler(CommandHandler("week", handlers.week))
    application.add_handler(CommandHandler("month", handlers.month))
    application.add_handler(CommandHandler("undo", handlers.undo))
    application.add_handler(CommandHandler("export", handlers.export))
    application.add_handler(CommandHandler(["language", "dil"], handlers.language_command))
    application.add_handler(CallbackQueryHandler(handlers.language_selected, pattern=r"^lang:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.log_expense))

    logger.info("Starting bot (db_path=%s)", db_path)
    application.run_polling()


if __name__ == "__main__":
    main()
