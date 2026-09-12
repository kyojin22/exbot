# Changelog

## 2026-09-12 — Claude Code

Added English/Turkish multi-language support per the feature spec.

- Added `bot/i18n.py` — `STRINGS` dict (en/tr) covering every bot-facing message (welcome, help, expense-logged, summaries, undo, export, not-allowed, language picker), and `t(key, lang, **kwargs)` with fallback to English then to the raw key.
- Reworked `bot/categories.py`: category keys are now canonical, language-independent (`"food"`, `"transport"`, `"bills"`, `"health"`, `"entertainment"`, `"shopping"`, `"uncategorized"` — renamed from `"Housing"` to `"bills"` to match the spec's `CATEGORY_DISPLAY`), with a new `CATEGORY_DISPLAY` mapping and `get_category_display(key, lang)` helper. `CATEGORY_KEYWORDS` now mixes English and Turkish keywords per category (matching is language-independent — Turkish words are detected even if the chat's display language is English, and vice versa).
- `bot/parser.py`: `#tag` category override now lowercases to a canonical key instead of `.capitalize()`-ing to a display string.
- `bot/db.py`: added `user_settings` table (`chat_id` PK, `language`) plus `has_language_preference`, `get_user_language` (defaults to `"en"`), `set_user_language` (upsert).
- `bot/handlers.py`: every reply now goes through `t()` using the chat's stored language; added `/language` and `/dil` (alias) showing an inline English/Türkçe keyboard, and a `language_selected` callback handler that persists the choice and replies with a confirmation in the just-selected language. `/start` on a brand-new chat_id shows the language picker first, then the translated welcome text right after a first-time selection. `restricted` decorator now also handles callback queries and replies with a translated "not allowed" message.
- `bot/main.py`: registered `CommandHandler(["language", "dil"], ...)` and a `CallbackQueryHandler` for the `lang:en` / `lang:tr` callback data.
- Updated `tests/test_parser.py` for lowercase canonical category keys (`"Food"` → `"food"`, `"Housing"` → `"bills"`, etc.) and added two tests for Turkish keyword detection (`kahve` → `food`, `taksi` → `transport`).
- Added `tests/test_i18n.py`: `t()` en/tr lookups, fallback-to-English, fallback-to-key, and `get_user_language`/`set_user_language`/`has_language_preference` round-trips against a temp SQLite DB. All 25 tests pass (15 parser + 8 i18n, up from 15).

Known follow-up (not done, needs your go-ahead since it touches live data): the 3 expenses already in `data/expenses.db` were logged before this change and have old-style capitalized categories (`"Food"`, `"Transport"`) rather than the new canonical lowercase keys — they still display correctly in English but won't translate to Turkish. A one-time migration (lowercase existing `category` values) would fix this; not run yet.

## 2026-08-22 (3) — Claude Code

Personalized the `/start` welcome message; confirmed multi-user (family) support needs no code changes.

- `/start` now builds its reply dynamically (`_build_welcome_text` in `bot/handlers.py`) — greets the user by their Telegram first name, lists all commands inline (not just a pointer to `/help`), and states that expense data is private per chat_id.
- No DB/handler changes were needed for multiple family members: every query in `bot/db.py` is already scoped by `chat_id`, so each person who DMs the bot privately already gets fully isolated `/today` `/week` `/month` `/undo` `/export` and history. Adding a family member is just appending their chat ID to the comma-separated `ALLOWED_CHAT_IDS` in `.env` and restarting.

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
