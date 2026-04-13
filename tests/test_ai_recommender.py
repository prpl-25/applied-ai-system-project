"""
Unit tests for src/ai_recommender.py.

These tests do NOT require an Anthropic API key or any network access.
They test the tool handler functions and catalog utilities in isolation.
"""

import json

import pytest

from src.ai_recommender import (
    build_catalog_index,
    execute_tool,
    handle_get_catalog_info,
    handle_get_song_recommendations,
)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

SAMPLE_SONGS = [
    {
        "id": 1,
        "title": "Sunburst",
        "artist": "Pop Star",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.9,
        "tempo_bpm": 128.0,
        "valence": 0.85,
        "danceability": 0.8,
        "acousticness": 0.1,
    },
    {
        "id": 2,
        "title": "Night Drift",
        "artist": "Lo Beats",
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.3,
        "tempo_bpm": 75.0,
        "valence": 0.4,
        "danceability": 0.5,
        "acousticness": 0.7,
    },
    {
        "id": 3,
        "title": "Storm Runner",
        "artist": "Voltline",
        "genre": "rock",
        "mood": "intense",
        "energy": 0.93,
        "tempo_bpm": 150.0,
        "valence": 0.6,
        "danceability": 0.7,
        "acousticness": 0.05,
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_build_catalog_index_returns_correct_keys():
    index = build_catalog_index(SAMPLE_SONGS)
    assert "genres" in index
    assert "moods" in index
    assert "energy_range" in index
    assert sorted(index["genres"]) == ["lofi", "pop", "rock"]
    assert sorted(index["moods"]) == ["chill", "happy", "intense"]
    assert len(index["energy_range"]) == 2
    assert index["energy_range"][0] == pytest.approx(0.3)
    assert index["energy_range"][1] == pytest.approx(0.93)


def test_handle_get_song_recommendations_valid_input():
    result_str = handle_get_song_recommendations(
        {"genre": "pop", "mood": "happy", "energy": 0.9}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    assert "songs" in result
    assert len(result["songs"]) >= 1
    first = result["songs"][0]
    assert "title" in first
    assert "score" in first
    assert "explanation" in first


def test_handle_get_song_recommendations_unknown_genre_returns_warning():
    result_str = handle_get_song_recommendations(
        {"genre": "drum and bass", "mood": "happy", "energy": 0.5}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    assert "warning" in result
    assert result["songs"] == []
    assert "available_genres" in result
    assert "pop" in result["available_genres"]


def test_handle_get_song_recommendations_unknown_mood_returns_warning():
    result_str = handle_get_song_recommendations(
        {"genre": "pop", "mood": "euphoric", "energy": 0.5}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    assert "warning" in result
    assert result["songs"] == []
    assert "available_moods" in result


def test_handle_get_song_recommendations_energy_clamped():
    # energy=2.5 is out of range — should not raise, should clamp and return results
    result_str = handle_get_song_recommendations(
        {"energy": 2.5}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    assert "songs" in result
    # All songs should still be returned (k defaults to 5, we have 3 songs)
    assert len(result["songs"]) > 0


def test_execute_tool_unknown_tool_name_returns_error():
    result_str = execute_tool("nonexistent_tool", {}, SAMPLE_SONGS)
    result = json.loads(result_str)
    assert "error" in result


def test_handle_get_catalog_info():
    result_str = handle_get_catalog_info(SAMPLE_SONGS)
    result = json.loads(result_str)
    assert "genres" in result
    assert "pop" in result["genres"]
    assert "lofi" in result["genres"]
    assert "energy_range" in result
    assert len(result["energy_range"]) == 2
    assert isinstance(result["energy_range"][0], float)
    assert isinstance(result["energy_range"][1], float)


def test_results_include_confidence_pct_in_valid_range():
    """Every song result must include a confidence_pct between 0 and 100."""
    result_str = handle_get_song_recommendations(
        {"genre": "pop", "mood": "happy", "energy": 0.9}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    for song in result["songs"]:
        assert "confidence_pct" in song, "confidence_pct missing from result"
        assert 0.0 <= song["confidence_pct"] <= 100.0, (
            f"confidence_pct {song['confidence_pct']} out of [0, 100]"
        )


def test_results_are_sorted_by_score_descending():
    """Recommendations must always come back in descending score order."""
    result_str = handle_get_song_recommendations({"energy": 0.5}, SAMPLE_SONGS)
    result = json.loads(result_str)
    scores = [s["score"] for s in result["songs"]]
    assert scores == sorted(scores, reverse=True), (
        f"Results not sorted descending: {scores}"
    )


def test_perfect_match_has_high_confidence():
    """A song that exactly matches genre, mood, and energy should score above 90%."""
    # SAMPLE_SONGS contains pop/happy/0.9 — request same profile
    result_str = handle_get_song_recommendations(
        {"genre": "pop", "mood": "happy", "energy": 0.9, "k": 1}, SAMPLE_SONGS
    )
    result = json.loads(result_str)
    top = result["songs"][0]
    assert top["confidence_pct"] >= 90.0, (
        f"Expected >= 90% confidence for perfect match, got {top['confidence_pct']}%"
    )
