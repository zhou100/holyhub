import pytest
from fastapi.testclient import TestClient
from holyhub.database import Database
from backend.main import app
from backend import deps


@pytest.fixture(autouse=True)
def use_test_db(tmp_path):
    """Replace the shared db with an in-memory test db for each test."""
    test_db = Database(db_path=str(tmp_path / "test.db"))
    test_db.connect()
    # Seed one church and one review
    test_db.execute_insert(
        "INSERT INTO Churches (name, address, city, state, denomination, service_times) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("Test Church", "1 Main St", "Brooklyn", "NY", "Non-denom", "Sun 10am"),
    )
    test_db.execute_insert(
        "INSERT INTO Reviews (church_id, rating, worship_energy, community_warmth, "
        "sermon_depth, childrens_programs, theological_openness, facilities) "
        "VALUES (1, 5.0, 5.0, 4.5, 4.0, 4.0, 3.5, 4.2)",
        (),
    )
    deps.db = test_db
    yield
    test_db.close_connection()
    deps.db = Database()  # restore singleton type


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_list_churches_returns_results(client):
    r = client.get("/api/churches?city=Brooklyn&state=NY")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Church"


def test_list_churches_includes_avg_rating(client):
    r = client.get("/api/churches?city=Brooklyn&state=NY")
    church = r.json()[0]
    assert church["avg_rating"] == 5.0
    assert church["review_count"] == 1


def test_list_churches_empty_city(client):
    r = client.get("/api/churches?city=Nowhere&state=XX")
    assert r.status_code == 200
    assert r.json() == []


def test_church_detail_200(client):
    r = client.get("/api/churches/1")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Test Church"
    assert "dimensions" in data
    assert set(data["dimensions"].keys()) == {
        "worship_energy", "community_warmth", "sermon_depth",
        "childrens_programs", "theological_openness", "facilities",
    }


def test_church_detail_404(client):
    r = client.get("/api/churches/9999")
    assert r.status_code == 404


def test_church_detail_dimensions_rounded(client):
    r = client.get("/api/churches/1")
    dims = r.json()["dimensions"]
    assert dims["worship_energy"] == 5.0
    assert dims["community_warmth"] == 4.5


def test_similar_churches_returns_list(client):
    r = client.get("/api/churches/1/similar")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_similar_churches_excludes_self(client):
    r = client.get("/api/churches/1/similar")
    assert 1 not in [c["id"] for c in r.json()]


def test_similar_churches_404_for_missing(client):
    r = client.get("/api/churches/9999/similar")
    assert r.status_code == 404
