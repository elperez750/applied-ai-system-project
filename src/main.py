"""
Command line runner for the Music Recommender Simulation.
Run with: python -m src.main
"""

from recommender import load_songs, recommend_songs, DEFAULT_WEIGHTS


# ── Helper ────────────────────────────────────────────────────────────────────

def print_recommendations(label: str, user_prefs: dict, recommendations: list) -> None:
    """Print a labelled block of top-k recommendations to the terminal."""
    print("\n" + "=" * 56)
    print(f"  {label}")
    print(f"  Genre: {user_prefs.get('genre')} | Mood: {user_prefs.get('mood')} | "
          f"Energy: {user_prefs.get('energy')} | Acoustic: {user_prefs.get('likes_acoustic', False)}")
    print("=" * 56)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       {song['genre']} | {song['mood']} | energy {song['energy']}")
        print(f"       Score: {score:.2f}  |  {explanation}")
    print()


# ── Profiles ──────────────────────────────────────────────────────────────────

PROFILES = [
    (
        "Profile 1: High-Energy Pop",
        {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False},
    ),
    (
        "Profile 2: Chill Lofi Study Session",
        {"genre": "lofi", "mood": "chill", "energy": 0.38, "likes_acoustic": True},
    ),
    (
        "Profile 3: Deep Intense Rock",
        {"genre": "rock", "mood": "intense", "energy": 0.90, "likes_acoustic": False},
    ),
    (
        # Adversarial: genre=ambient (calm, quiet songs) but mood=intense and energy=0.90
        # No ambient song in the catalog is also intense — exposes genre over-weighting.
        "Profile 4 (Adversarial): Ambient + Intense + High Energy",
        {"genre": "ambient", "mood": "intense", "energy": 0.90, "likes_acoustic": False},
    ),
]

# Experiment: halve genre weight, double energy weight
EXPERIMENTAL_WEIGHTS = {"genre": 1.0, "mood": 1.0, "energy": 2.0, "acoustic": 0.5}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded {len(songs)} songs.")

    k = 5

    # --- Run all standard profiles ---
    for label, user_prefs in PROFILES:
        recs = recommend_songs(user_prefs, songs, k=k)
        print_recommendations(label, user_prefs, recs)

    # --- Step 3 experiment: weight shift on the adversarial profile ---
    adv_label, adv_prefs = PROFILES[3]

    print("\n" + "#" * 56)
    print("  EXPERIMENT: Weight Shift on Adversarial Profile")
    print("  Default  → genre +2.0, energy weight x1.0")
    print("  Modified → genre +1.0, energy weight x2.0")
    print("#" * 56)

    recs_default = recommend_songs(adv_prefs, songs, k=k, weights=DEFAULT_WEIGHTS)
    print_recommendations("Adversarial — DEFAULT weights", adv_prefs, recs_default)

    recs_exp = recommend_songs(adv_prefs, songs, k=k, weights=EXPERIMENTAL_WEIGHTS)
    print_recommendations("Adversarial — EXPERIMENTAL weights", adv_prefs, recs_exp)

    print("Observation: with default weights, low-energy ambient songs dominate")
    print("because genre match (+2.0) outweighs the large energy gap.")
    print("Doubling the energy weight lets high-energy intense tracks rise to the top.\n")


if __name__ == "__main__":
    main()
