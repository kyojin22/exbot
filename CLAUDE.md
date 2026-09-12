# CLAUDE.md — Telegram Expense Tracker Bot

This file guides Claude Code (or any AI coding assistant) when working on this project.
It defines the goal, architecture, and conventions so future sessions don't need to be
re-explained from scratch. Deployment will be handled separately via GitHub Actions.

read also CHANGELOG.md to understand remember what happened last

---

## 1. Project Goal

A personal Telegram bot that lets me log expenses by just texting it naturally, e.g.:

```
50000 lunch
15000 coffee
20 usd taxi to airport
30 eur hotel deposit
```

The bot parses the message, extracts amount + category/description, saves it, and
replies with a confirmation. I can also ask it for summaries (daily/weekly/monthly)
and export data.

This is a **personal, single-user (or small trusted group) project** — not a commercial
product. Keep things simple, cheap to run, and low-maintenance.

**Primary currency: UZS** (Uzbekistani som). The bot should also support entering
other currencies inline using a 3-letter ISO code (USD, EUR, UZS, etc.) directly in
the message, e.g. `50000 uzs lunch` or `20 usd taxi`. If no currency code is given,
default to `UZS`.

---

## 2. Core Features (MVP)

- [ ] Receive a text message like `50000 lunch` and parse: amount, currency (default UZS, or 3-letter code if given), category, note
- [ ] Store each expense (timestamp, amount, category, note, raw message)
- [ ] Reply with a confirmation: `✅ Logged 50,000 UZS — Lunch (Food)` (or `✅ Logged 20 USD — Taxi (Transport)`)
- [ ] `/today` — sum of today's expenses
- [ ] `/week` — sum of this week's expenses
- [ ] `/month` — sum of this month's expenses, broken down by category
- [ ] `/undo` — delete the last logged entry
- [ ] `/export` — send a CSV of all expenses
- [ ] Basic category auto-detection (keywords: "lunch/coffee/food" → Food, "uber/taxi/bus" → Transport, etc.), with manual override like `$20 lunch #food`
- [ ] Optional manual date at the end of the message in `DD.MM.YYYY` format (e.g. `50000 lunch 20.07.2026`) — if not present, default to the current date/time

### Stretch features (later)
- [ ] Voice message support (transcribe → parse)
- [ ] Monthly budget alerts ("You've spent 80% of your Food budget")
- [ ] Live exchange rates to convert everything to UZS for combined totals
- [ ] Simple web dashboard (charts) reading from the same database
- [ ] Recurring expense reminders

---

## 3. Tech Stack

- **Language:** Python 3.11+
- **Telegram library:** `python-telegram-bot` (v20+, async)
- **Database:** SQLite (simple, file-based, perfect for single-user). Can migrate to
  Postgres later if it grows.
- **Env config:** `.env` file + `python-dotenv` (never commit secrets)
- **Optional later:** FastAPI for a small web dashboard

Keep dependencies minimal. Avoid adding a framework unless it's clearly needed.

---

## 4. Project Structure

```
telegram-expense-bot/
├── CLAUDE.md              # this file
├── README.md              # setup/run instructions for humans
├── .env.example            # template for secrets (BOT_TOKEN, etc.)
├── .gitignore
├── requirements.txt
├── bot/
│   ├── __init__.py
│   ├── main.py              # entry point, starts the bot
│   ├── handlers.py          # message + command handlers
│   ├── parser.py            # expense text parsing logic
│   ├── db.py                 # SQLite setup + queries
│   ├── categories.py        # keyword → category mapping
│   └── currencies.py        # allow-list of supported 3-letter currency codes
└── data/
    └── expenses.db          # SQLite file (gitignored)
```

---

## 5. Data Model

Single table `expenses`:

| column     | type      | notes                          |
|------------|-----------|---------------------------------|
| id         | INTEGER PK AUTOINCREMENT | |
| chat_id    | INTEGER   | Telegram chat/user id            |
| amount     | REAL      | positive number                  |
| currency   | TEXT      | 3-letter code, default "UZS"     |
| category   | TEXT      | auto-detected or manual          |
| note       | TEXT      | free text description            |
| raw_message| TEXT      | original message, for debugging  |
| created_at | TEXT      | ISO timestamp; the expense date — either parsed from a manual `DD.MM.YYYY` at the end of the message, or the current date/time if not provided |

---

## 6. Message Parsing Rules

The parser (`bot/parser.py`) should handle formats like:

- `50000 lunch` → 50,000 UZS, category from keyword match
- `20 usd taxi to airport` → 20 USD
- `30 eur hotel deposit` → 30 EUR
- `50000 uzs lunch #food` (explicit category override with `#tag`)
- `15000 coffee` → 15,000 UZS (no currency code given → defaults to UZS)
- `50000 lunch 20.07.2026` → logged with date 2026-07-20 instead of today
- `20 usd taxi 05.01.2026 #transport` → date + explicit category together

Logic:
1. Extract the first number in the message (digits, optional decimal point,
   optional thousands separators like `50,000` or `50000`) → `amount`
2. Look at the token immediately following the number: if it matches a known
   3-letter currency code (case-insensitive — `usd`, `eur`, `uzs`, `rub`, `gbp`, etc.,
   from a small allow-list in `bot/currencies.py`), use it as `currency` and consume
   that token from the message
3. If no currency code token is found, default `currency` to `DEFAULT_CURRENCY` (UZS)
4. Check the **end of the message** for a date in `DD.MM.YYYY` format (e.g.
   `20.07.2026`). If found and valid, use it as the expense date and consume that
   token from the message. If not found, default the expense date to "now"
   (current date/time)
5. If a `#category` tag exists, use it as the category
6. Otherwise, run keyword matching against `categories.py` mapping
7. If no category matches, default to `"Uncategorized"`
8. Everything remaining after removing the amount, currency code, date, and `#tag`
   (if present) → `note`
9. If no number is found in the message, reply with a help hint instead of logging
   anything

The date and `#tag` can appear in any order at the end of the message (e.g. both
`50000 lunch 20.07.2026 #food` and `50000 lunch #food 20.07.2026` should work) —
strip them independently rather than assuming a fixed order.

Keep the currency allow-list small and explicit (just the codes you actually use —
e.g. `UZS`, `USD`, `EUR`, `RUB`) rather than trying to support all ISO 4217 codes.
This avoids false positives where a normal word in the note accidentally looks like
a currency code.

Keep this logic in **pure functions** that are easy to unit test — don't mix parsing
logic with Telegram API calls.

---

## 7. Environment Variables (.env)

```
BOT_TOKEN=your_telegram_bot_token_here
ALLOWED_CHAT_IDS=123456789        # comma-separated; only these users/chats can log expenses
DEFAULT_CURRENCY=UZS
SUPPORTED_CURRENCIES=UZS,USD,EUR,RUB   # comma-separated allow-list of 3-letter codes
DB_PATH=./data/expenses.db
```

`ALLOWED_CHAT_IDS` is important — since this is personal, the bot should ignore or
politely refuse messages from anyone not in this list.

---

## 8. Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in BOT_TOKEN etc.
python -m bot.main
```

Use **polling** (not webhooks) for simplicity — no public domain/SSL cert needed.

---

## 10. Deployment

Deployment details are not finalized yet — to be figured out separately.

Plan: automate releases with **GitHub Actions**. On push (or on release), a workflow
will SSH into the server using a stored secret (SSH key) and a **low-privilege user**
dedicated to this bot (not root), pull the latest code, and restart the service.
No manual deployment steps needed once this is set up.

---

## 11. Security Notes

- Never commit `.env` or `data/expenses.db` — both are in `.gitignore`
- Restrict the bot to `ALLOWED_CHAT_IDS` so random people who find the bot username
  can't log fake data or see your commands
- The deploy user (used by GitHub Actions) should have the minimum permissions
  needed to update and restart the bot — nothing more

---

## 12. Coding Conventions

- Type hints on all functions
- Keep handlers thin — business logic (parsing, DB queries) lives in separate modules
- Prefer plain SQL over an ORM for this small a project (keep it simple)
- Write docstrings for parser functions since they're the trickiest part
- Add basic unit tests for `parser.py` in `tests/test_parser.py` once MVP works

---

## 13. Current Status / Next Steps

> Update this section as the project progresses so future sessions know where things stand.

- [x] Repo initialized
- [x] MVP parsing + logging working locally (parser, categories, currencies, db, handlers, main all implemented; unit tests passing)
- [x] Bot smoke-tested against a real Telegram token (getMe/deleteWebhook/getUpdates/sendMessage all confirmed working)
- [x] English/Turkish multi-language support (`/language`, `/dil`, `bot/i18n.py`, per-chat `user_settings.language`)
- [ ] One-time migration of the 3 pre-existing expense rows to lowercase canonical category keys (old rows still show fine in English, just won't translate to Turkish until migrated)
- [ ] GitHub Actions deployment workflow set up (Dockerfile/docker-compose already added in a prior session)

## 14. Changelog after each prompt

After, you complete the task or prompt write your name and what did you do during the session in CHANGELOG.md
