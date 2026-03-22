from backend.utils import compute_tags


def test_no_tags_when_fewer_than_3_reviews():
    dims = {"worship_energy": 5.0, "community_warmth": 5.0, "sermon_depth": 5.0,
            "childrens_programs": 5.0, "theological_openness": 5.0, "facilities": 5.0}
    assert compute_tags(dims, 2) == []
    assert compute_tags(dims, 0) == []


def test_vibrant_worship_tag():
    dims = {"worship_energy": 4.6, "community_warmth": 3.0, "sermon_depth": 3.0,
            "childrens_programs": 3.0, "theological_openness": 3.0, "facilities": 3.0}
    assert "Vibrant worship" in compute_tags(dims, 5)


def test_no_vibrant_worship_below_threshold():
    dims = {"worship_energy": 4.5, "community_warmth": 3.0, "sermon_depth": 3.0,
            "childrens_programs": 3.0, "theological_openness": 3.0, "facilities": 3.0}
    assert "Vibrant worship" not in compute_tags(dims, 5)


def test_traditional_tag():
    dims = {"worship_energy": 3.0, "community_warmth": 3.0, "sermon_depth": 3.0,
            "childrens_programs": 3.0, "theological_openness": 2.4, "facilities": 3.0}
    assert "Traditional" in compute_tags(dims, 5)


def test_progressive_tag():
    dims = {"worship_energy": 3.0, "community_warmth": 3.0, "sermon_depth": 3.0,
            "childrens_programs": 3.0, "theological_openness": 4.1, "facilities": 3.0}
    assert "Progressive" in compute_tags(dims, 5)


def test_none_dimensions_do_not_crash():
    """SQL AVG() returns None for missing dims — must not raise TypeError."""
    dims = {"worship_energy": None, "community_warmth": None, "sermon_depth": None,
            "childrens_programs": None, "theological_openness": None, "facilities": None}
    result = compute_tags(dims, 5)
    assert isinstance(result, list)
    assert result == []


def test_partial_none_dimensions():
    dims = {"worship_energy": 4.8, "community_warmth": None, "sermon_depth": None,
            "childrens_programs": None, "theological_openness": None, "facilities": None}
    tags = compute_tags(dims, 5)
    assert "Vibrant worship" in tags


def test_kids_programs_tag():
    dims = {"worship_energy": 3.0, "community_warmth": 3.0, "sermon_depth": 3.0,
            "childrens_programs": 4.1, "theological_openness": 3.0, "facilities": 3.0}
    assert "Kids programs" in compute_tags(dims, 5)


def test_multiple_tags():
    dims = {"worship_energy": 4.8, "community_warmth": 4.8, "sermon_depth": 3.0,
            "childrens_programs": 3.0, "theological_openness": 3.0, "facilities": 3.0}
    tags = compute_tags(dims, 10)
    assert "Vibrant worship" in tags
    assert "Strong community" in tags
