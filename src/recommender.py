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
        scored = []
        for song in self.songs:
            score, _ = self._score(user, song)
            scored.append((song, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = self._score(user, song)
        return ", ".join(reasons) if reasons else "No strong match found"

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []

        if song.genre == user.favorite_genre:
            score += 2.0
            reasons.append(f"genre match ({song.genre})")

        if song.mood == user.favorite_mood:
            score += 1.0
            reasons.append(f"mood match ({song.mood})")

        energy_similarity = 1.0 - abs(song.energy - user.target_energy)
        score += energy_similarity
        reasons.append(f"energy similarity {energy_similarity:.2f}")

        if user.likes_acoustic and song.acousticness >= 0.70:
            score += 0.5
            reasons.append("acoustic preference match")

        return score, reasons


def load_songs(csv_path: str) -> List[Dict]:
    """Read a CSV of songs and return a list of dicts with numeric fields cast to float/int."""
    songs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                'id': int(row['id']),
                'title': row['title'],
                'artist': row['artist'],
                'genre': row['genre'],
                'mood': row['mood'],
                'energy': float(row['energy']),
                'tempo_bpm': float(row['tempo_bpm']),
                'valence': float(row['valence']),
                'danceability': float(row['danceability']),
                'acousticness': float(row['acousticness']),
            })
    return songs


DEFAULT_WEIGHTS = {"genre": 2.0, "mood": 1.0, "energy": 1.0, "acoustic": 0.5}


def score_song(user_prefs: Dict, song: Dict, weights: Dict = None) -> Tuple[float, List[str]]:
    """Score one song against user preferences; returns (total_score, list_of_reasons)."""
    # Algorithm Recipe (default weights):
    #   +2.0  genre match          (weights["genre"])
    #   +1.0  mood match           (weights["mood"])
    #   +0–1  energy similarity    weights["energy"] * (1.0 - |song_energy - target_energy|)
    #   +0.5  acoustic bonus       (only when likes_acoustic=True and acousticness >= 0.70)
    w = weights if weights is not None else DEFAULT_WEIGHTS
    score = 0.0
    reasons = []

    if song['genre'] == user_prefs.get('genre'):
        pts = w["genre"]
        score += pts
        reasons.append(f"genre match (+{pts})")

    if song['mood'] == user_prefs.get('mood'):
        pts = w["mood"]
        score += pts
        reasons.append(f"mood match (+{pts})")

    target_energy = user_prefs.get('energy', 0.5)
    energy_similarity = w["energy"] * (1.0 - abs(song['energy'] - target_energy))
    score += energy_similarity
    reasons.append(f"energy score {energy_similarity:.2f}")

    if user_prefs.get('likes_acoustic') and song['acousticness'] >= 0.70:
        pts = w["acoustic"]
        score += pts
        reasons.append(f"acoustic match (+{pts})")

    return (score, reasons)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, weights: Dict = None) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest-first, and return the top-k as (song, score, explanation) tuples."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights=weights)
        explanation = ", ".join(reasons)
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
