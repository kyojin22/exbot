# Changelog

## 2026-08-22 (2) — Claude Code

Fixed a startup crash and added a `/help` command.

- Fixed `AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb'` on `Application.builder().build()` — `python-telegram-bot` 20.8 isn't compatible with the installed Python 3.14. Upgraded to `python-telegram-bot` 22.8 (bumped `requirements.txt` to `>=21,<23`) and confirmed the bot connects to the real Telegram API (`getMe`/`deleteWebhook`/`getUpdates` all 200 OK).
- Added `/help` command (`bot/handlers.py: help_command`, registered in `bot/main.py`) — builds its text dynamically from `bot/currencies.py` and `bot/categories.py` (`_build_help_text`) so the command format guide, supported currency list, and category-keyword list can never drift out of sync with the actual code. Renamed the old parse-failure hint from `HELP_TEXT` to `PARSE_ERROR_TEXT` to avoid confusion with the new `/help` command, and pointed both `/start` and the parse-failure message at `/help`.
- Updated README's command list.

## 2026-08-22 — Claude Code

Built the MVP from scratch per CLAUDE.md.

- Added `bot/currencies.py` — env-driven allow-list of supported 3-letter currency codes (default UZS, USD/EUR/RUB).
- Added `bot/categories.py` — keyword → category auto-detection (`detect_category`), falls back to "Uncategorized".
- Added `bot/parser.py` — pure-function `parse_expense()` implementing the full parsing spec from section 6: amount extraction (with thousands separators/decimals), currency-code token right after the amount, trailing `DD.MM.YYYY` date and `#tag` in either order, remaining text as note. Returns `None` when no amount is found.
- Added `bot/db.py` — SQLite schema (`expenses` table) + plain-SQL queries: `init_db`, `insert_expense`, `get_expenses_since`, `get_all_expenses`, `get_last_expense`, `delete_expense`.
- Added `bot/handlers.py` — Telegram handlers: free-text message logging with confirmation reply, `/start`, `/today`, `/week`, `/month` (with per-category breakdown), `/undo`, `/export` (CSV via `reply_document`). `@restricted` decorator enforces `ALLOWED_CHAT_IDS`.
- Added `bot/main.py` — loads `.env`, initializes the DB, wires up `python-telegram-bot` v20 `Application`, runs polling.
- Added `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `data/.gitkeep`.
- Added `tests/test_parser.py` — 15 unit tests covering every example format in CLAUDE.md section 6 (currency detection, date+tag in both orders, thousands separators, invalid dates, empty notes, unknown currency-like words, decimals). All passing.
- Smoke-tested `bot/db.py` CRUD directly and confirmed `bot/main.py` / `bot/handlers.py` import cleanly.
- Updated section 13 status checklist in CLAUDE.md.

Not done yet: no real Telegram `BOT_TOKEN` was available in this session, so the bot has not been run end-to-end against the live Telegram API — only the parser/db/import layers were verified. GitHub Actions deployment workflow is still unset.
