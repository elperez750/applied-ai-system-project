import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from chat import parse_query


def test_study_query_returns_focused_mood():
    prefs = parse_query("I need something to study to and focus")
    assert prefs["mood"] == "focused"


def test_workout_query_returns_high_energy():
    prefs = parse_query("high energy gym music to work out to")
    assert prefs["energy"] == 0.9


def test_acoustic_query_sets_likes_acoustic():
    prefs = parse_query("acoustic guitar music please")
    assert prefs["likes_acoustic"] is True


def test_moody_query_returns_moody_mood():
    prefs = parse_query("something sad and rainy day vibes")
    assert prefs["mood"] == "moody"


def test_jazz_query_returns_jazz_genre():
    prefs = parse_query("jazz for a coffee shop afternoon")
    assert prefs["genre"] == "jazz"


def test_chill_query_returns_low_energy():
    prefs = parse_query("something slow and gentle to wind down")
    assert prefs["energy"] == 0.25


def test_unknown_query_returns_safe_defaults():
    prefs = parse_query("xyzzy blorp")
    assert prefs["genre"] is None
    assert prefs["mood"] is None
    assert prefs["energy"] == 0.5
    assert prefs["likes_acoustic"] is False


def test_empty_query_returns_safe_defaults():
    prefs = parse_query("")
    assert prefs["genre"] is None
    assert prefs["mood"] is None
    assert prefs["energy"] == 0.5
