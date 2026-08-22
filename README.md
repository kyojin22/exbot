# Telegram Expense Tracker Bot

A personal Telegram bot for logging expenses by texting naturally, e.g.:

```
50000 lunch
15000 coffee
20 usd taxi to airport
30 eur hotel deposit
```

See [CLAUDE.md](CLAUDE.md) for the full design/spec.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in BOT_TOKEN and ALLOWED_CHAT_IDS
python -m bot.main
```

Uses **polling**, so no public domain/SSL cert is needed.

## Commands

- Just send a message like `50000 lunch` or `20 usd taxi to airport` to log an expense.
- `/today` — sum of today's expenses
- `/week` — sum of this week's expenses
- `/month` — sum of this month's expenses, broken down by category
- `/undo` — delete the last logged entry
- `/export` — download a CSV of all your expenses
- `/help` — full in-bot guide: every command, message format, supported currencies, and auto-detected category keywords

## Message format

- First number in the message is the amount (`50000`, `50,000`, `20.5`, ...)
- Followed by an optional 3-letter currency code (`usd`, `eur`, `uzs`, `rub`) — defaults to `UZS`
- Optional `#category` tag to override auto-detected category
- Optional trailing date in `DD.MM.YYYY` format — defaults to now
- Everything else becomes the note

Date and `#tag` can appear in either order at the end of the message.

## Tests

```bash
pip install pytest
pytest
```
