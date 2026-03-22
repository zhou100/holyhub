import pytest
from fastapi.testclient import TestClient
from holyhub.database import Database
from backend.main import app
from backend import deps


@pytest.fixture(autouse=True)
def use_test_db(tmp_path):
    test_db = Database(db_path=str(tmp_path / "test.db"))
    test_db.connect()
    test_db.execute_insert(
        "INSERT INTO Churches (name, city, state) VALUES (?, ?, ?)",
        ("Grace Church", "Brooklyn", "NY"),
    )
    test_db.execute_insert(
        "INSERT INTO Reviews (church_id, rating, worship_energy, comment) VALUES (1, 4.0, 4.5, ?)",
        ("Great worship!",),
    )
    deps.db = test_db
    yield
    test_db.close_connection()
    deps.db = Database()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_get_reviews_returns_structure(client):
    r = client.get("/api/reviews/1")
    assert r.status_code == 200
    data = r.json()
    assert "reviews" in data
    assert "dimensions" in data


def test_get_reviews_list(client):
    r = client.get("/api/reviews/1")
    reviews = r.json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["rating"] == 4.0
    assert reviews[0]["comment"] == "Great worship!"


def test_get_reviews_dimensions_aggregated(client):
    r = client.get("/api/reviews/1")
    dims = r.json()["dimensions"]
    assert dims["worship_energy"] == 4.5
    # dimensions with no data are None
    assert dims["community_warmth"] is None


def test_get_reviews_empty_church(client):
    r = client.get("/api/reviews/9999")
    assert r.status_code == 200
    data = r.json()
    assert data["reviews"] == []


def test_post_review_returns_id(client):
    r = client.post("/api/reviews", json={
        "church_id": 1,
        "rating": 5,
        "comment": "Amazing",
        "worship_energy": 5.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert "review_id" in data
    assert data["review_id"] > 0


def test_post_review_invalid_rating(client):
    r = client.post("/api/reviews", json={"church_id": 1, "rating": 6})
    assert r.status_code == 422


def test_post_review_rating_below_range(client):
    r = client.post("/api/reviews", json={"church_id": 1, "rating": 0})
    assert r.status_code == 422


def test_post_review_no_auth_required(client):
    """Anonymous reviews must work without any auth header."""
    r = client.post("/api/reviews", json={"church_id": 1, "rating": 3})
    assert r.status_code == 201
