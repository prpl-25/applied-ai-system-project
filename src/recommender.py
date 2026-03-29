import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
        }
        ranked = sorted(
            self.songs,
            key=lambda song: score_song(user_prefs, song.__dict__)[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
        }
        _, reasons = score_song(user_prefs, song.__dict__)
        return "; ".join(reasons)


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song using the README formula and returns a score with reasons.

    Formula:
    score = 1 * genre_score + 1 * mood_score + 4 * energy_similarity
    where energy_similarity = 1 - abs(song_energy - user_energy)
    """
    reasons: List[str] = []

    genre_score = 1.0 if song.get("genre") == user_prefs.get("genre") else 0.0
    if genre_score == 1.0:
        reasons.append("genre match (+1.0)")
    else:
        reasons.append("genre mismatch (+0.0)")

    mood_score = 1.0 if song.get("mood") == user_prefs.get("mood") else 0.0
    if mood_score == 1.0:
        reasons.append("mood match (+1.0)")
    else:
        reasons.append("mood mismatch (+0.0)")

    user_energy = float(user_prefs.get("energy", 0.5))
    song_energy = float(song.get("energy", 0.5))
    energy_similarity = 1.0 - abs(song_energy - user_energy)
    energy_similarity = max(0.0, min(1.0, energy_similarity))
    energy_points = 4.0 * energy_similarity
    reasons.append(
        f"energy closeness {energy_similarity:.2f} (+{energy_points:.2f})"
    )

    total_score = 1.0 * genre_score + 1.0 * mood_score + energy_points
    return total_score, reasons

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            )
    return songs

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons)
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
