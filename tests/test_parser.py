from datetime import datetime

from bot.parser import parse_expense

NOW = datetime(2026, 8, 22, 12, 0, 0)


def test_amount_and_default_currency():
    parsed = parse_expense("50000 lunch", now=NOW)
    assert parsed.amount == 50000
    assert parsed.currency == "UZS"
    assert parsed.category == "food"
    assert parsed.note == "lunch"
    assert parsed.expense_date == NOW


def test_explicit_currency_usd():
    parsed = parse_expense("20 usd taxi to airport", now=NOW)
    assert parsed.amount == 20
    assert parsed.currency == "USD"
    assert parsed.category == "transport"
    assert parsed.note == "taxi to airport"


def test_explicit_currency_eur():
    parsed = parse_expense("30 eur hotel deposit", now=NOW)
    assert parsed.amount == 30
    assert parsed.currency == "EUR"
    assert parsed.category == "bills"
    assert parsed.note == "hotel deposit"


def test_explicit_currency_and_category_tag():
    parsed = parse_expense("50000 uzs lunch #food", now=NOW)
    assert parsed.amount == 50000
    assert parsed.currency == "UZS"
    assert parsed.category == "food"
    assert parsed.note == "lunch"


def test_no_currency_defaults_to_uzs():
    parsed = parse_expense("15000 coffee", now=NOW)
    assert parsed.amount == 15000
    assert parsed.currency == "UZS"
    assert parsed.category == "food"


def test_manual_date_at_end():
    parsed = parse_expense("50000 lunch 20.07.2026", now=NOW)
    assert parsed.amount == 50000
    assert parsed.note == "lunch"
    assert parsed.expense_date == datetime(2026, 7, 20)


def test_date_and_tag_together_date_then_tag():
    parsed = parse_expense("20 usd taxi 05.01.2026 #transport", now=NOW)
    assert parsed.amount == 20
    assert parsed.currency == "USD"
    assert parsed.category == "transport"
    assert parsed.note == "taxi"
    assert parsed.expense_date == datetime(2026, 1, 5)


def test_date_and_tag_together_tag_then_date():
    parsed = parse_expense("50000 lunch #food 20.07.2026", now=NOW)
    assert parsed.amount == 50000
    assert parsed.category == "food"
    assert parsed.note == "lunch"
    assert parsed.expense_date == datetime(2026, 7, 20)


def test_thousands_separator():
    parsed = parse_expense("50,000 lunch", now=NOW)
    assert parsed.amount == 50000


def test_no_number_returns_none():
    assert parse_expense("just some text", now=NOW) is None


def test_no_category_match_defaults_uncategorized():
    parsed = parse_expense("10000 something obscure", now=NOW)
    assert parsed.category == "uncategorized"


def test_unknown_currency_like_word_not_consumed():
    # "abc" isn't a supported currency code, so it stays part of the note
    parsed = parse_expense("100 abc test", now=NOW)
    assert parsed.currency == "UZS"
    assert parsed.note == "abc test"


def test_invalid_date_kept_in_note():
    parsed = parse_expense("50000 lunch 32.13.2026", now=NOW)
    assert parsed.expense_date == NOW
    assert parsed.note == "lunch 32.13.2026"


def test_empty_note_uses_category_fallback():
    parsed = parse_expense("50000 #food", now=NOW)
    assert parsed.note == ""
    assert parsed.category == "food"


def test_decimal_amount():
    parsed = parse_expense("20.5 usd snack", now=NOW)
    assert parsed.amount == 20.5
    assert parsed.currency == "USD"


def test_turkish_keyword_maps_to_food():
    parsed = parse_expense("50000 kahve", now=NOW)
    assert parsed.category == "food"


def test_turkish_keyword_maps_to_transport():
    parsed = parse_expense("20000 taksi", now=NOW)
    assert parsed.category == "transport"
