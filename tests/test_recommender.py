from src.recommender import Song, UserProfile, Recommender, score_song

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_adversarial_unknown_values_collapse_scores_to_zero():
    rec = make_small_recommender()
    user_prefs = {"genre": "drum and bass", "mood": "euphoric", "energy": 2.0}

    scores = [score_song(user_prefs, song.__dict__)[0] for song in rec.songs]

    assert scores == [0.0, 0.0]


def test_adversarial_nan_energy_grants_full_energy_points():
    rec = make_small_recommender()
    user_prefs = {"genre": "none", "mood": "none", "energy": float("nan")}

    scores = [score_song(user_prefs, song.__dict__)[0] for song in rec.songs]

    assert scores == [4.0, 4.0]


def test_adversarial_case_mismatch_lowers_score_despite_semantic_match():
    song = Song(
        id=3,
        title="Case Trap",
        artist="Test Artist",
        genre="pop",
        mood="happy",
        energy=0.9,
        tempo_bpm=118,
        valence=0.8,
        danceability=0.7,
        acousticness=0.3,
    )

    exact_score, _ = score_song({"genre": "pop", "mood": "happy", "energy": 0.9}, song.__dict__)
    case_mismatch_score, _ = score_song(
        {"genre": "Pop", "mood": "Happy", "energy": 0.9},
        song.__dict__,
    )

    assert exact_score == 6.0
    assert case_mismatch_score == 4.0


def test_edge_missing_energy_defaults_to_half():
    rec = make_small_recommender()
    song = rec.songs[0]

    missing_energy_score, _ = score_song({"genre": "pop", "mood": "happy"}, song.__dict__)
    explicit_half_score, _ = score_song(
        {"genre": "pop", "mood": "happy", "energy": 0.5},
        song.__dict__,
    )

    assert missing_energy_score == explicit_half_score
