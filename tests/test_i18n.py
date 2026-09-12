from bot import db
from bot.i18n import STRINGS, t


def test_t_returns_english():
    assert t("undo_nothing", "en") == "Nothing to undo."


def test_t_returns_turkish():
    assert t("undo_nothing", "tr") == "Geri alınacak bir şey yok."


def test_t_formats_kwargs():
    text = t("expense_logged_no_note", "en", amount="50,000", currency="UZS", category="Food")
    assert text == "✅ Logged 50,000 UZS (Food)"


def test_t_falls_back_to_english_for_missing_translation():
    # Temporarily register a key with only an English variant.
    STRINGS["_test_only_english"] = {"en": "hello"}
    try:
        assert t("_test_only_english", "tr") == "hello"
    finally:
        del STRINGS["_test_only_english"]


def test_t_falls_back_to_key_when_missing_entirely():
    assert t("_totally_unknown_key", "en") == "_totally_unknown_key"


def test_user_language_defaults_to_english(tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init_db(db_path)
    conn = db.get_connection(db_path)
    try:
        assert db.get_user_language(conn, chat_id=1) == "en"
        assert db.has_language_preference(conn, chat_id=1) is False
    finally:
        conn.close()


def test_set_user_language_roundtrip(tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init_db(db_path)
    conn = db.get_connection(db_path)
    try:
        db.set_user_language(conn, chat_id=1, language="tr")
        assert db.get_user_language(conn, chat_id=1) == "tr"
        assert db.has_language_preference(conn, chat_id=1) is True

        # Upsert: setting again overwrites rather than erroring.
        db.set_user_language(conn, chat_id=1, language="en")
        assert db.get_user_language(conn, chat_id=1) == "en"
    finally:
        conn.close()


def test_user_language_is_per_chat(tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init_db(db_path)
    conn = db.get_connection(db_path)
    try:
        db.set_user_language(conn, chat_id=1, language="tr")
        assert db.get_user_language(conn, chat_id=2) == "en"
    finally:
        conn.close()
