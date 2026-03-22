import sqlite3
import pytest
from holyhub.database import Database


@pytest.fixture
def db(tmp_path):
    db = Database(db_path=str(tmp_path / "test.db"))
    db.connect()
    db.execute_query(
        "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    yield db
    db.close_connection()


def test_execute_query_returns_rows(db):
    db.execute_query("INSERT INTO items (name) VALUES (?)", ("alpha",))
    db.connection.commit()
    rows = db.execute_query("SELECT id, name FROM items")
    assert len(rows) == 1
    assert rows[0]["name"] == "alpha"


def test_row_factory_named_access(db):
    db.execute_query("INSERT INTO items (name) VALUES (?)", ("beta",))
    db.connection.commit()
    rows = db.execute_query("SELECT id, name FROM items")
    # row_factory = sqlite3.Row → named access must work
    assert rows[0]["name"] == "beta"
    assert isinstance(rows[0], sqlite3.Row)


def test_execute_insert_returns_lastrowid(db):
    row_id = db.execute_insert("INSERT INTO items (name) VALUES (?)", ("gamma",))
    assert isinstance(row_id, int)
    assert row_id > 0


def test_execute_insert_sequential_ids(db):
    id1 = db.execute_insert("INSERT INTO items (name) VALUES (?)", ("x",))
    id2 = db.execute_insert("INSERT INTO items (name) VALUES (?)", ("y",))
    assert id2 == id1 + 1


def test_execute_query_no_connection(tmp_path):
    db = Database.__new__(Database)
    db.connection = None
    result = db.execute_query("SELECT 1")
    assert result == []
