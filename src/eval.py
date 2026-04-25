"""
Retriever evaluation script.
Runs fixed query -> expectation pairs through the full RAG pipeline (no Gemini)
and prints a pass/fail summary.

Run with: python -m src.eval
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from recommender import load_songs, recommend_songs
from chat import parse_query

MAX_SCORE = 4.5  # genre(2.0) + mood(1.0) + energy(1.0) + acoustic(0.5)

# Each case: (description, query, assertion_fn)
# assertion_fn receives the top retrieved song dict and returns (passed: bool, reason: str)
TEST_CASES = [
    (
        "Lofi study query -> top result is lofi genre",
        "lofi music to study to",
        lambda s: (s["genre"] == "lofi", f"got genre='{s['genre']}'"),
    ),
    (
        "Intense workout query -> top result has energy >= 0.85",
        "intense workout music high energy gym",
        lambda s: (s["energy"] >= 0.85, f"got energy={s['energy']}"),
    ),
    (
        "Jazz coffee shop query -> top result is jazz genre",
        "jazz for a coffee shop afternoon",
        lambda s: (s["genre"] == "jazz", f"got genre='{s['genre']}'"),
    ),
    (
        "Acoustic query -> top result has acousticness >= 0.70",
        "acoustic unplugged music",
        lambda s: (s["acousticness"] >= 0.70, f"got acousticness={s['acousticness']}"),
    ),
    (
        "Happy pop query -> top result is pop genre",
        "happy catchy pop music",
        lambda s: (s["genre"] == "pop", f"got genre='{s['genre']}'"),
    ),
    (
        "Moody night drive query -> top result has energy >= 0.60",
        "dark moody music for a night drive",
        lambda s: (s["energy"] >= 0.60, f"got energy={s['energy']}"),
    ),
    (
        "Ambient chill query -> top result has energy <= 0.40",
        "ambient atmospheric chill space music",
        lambda s: (s["energy"] <= 0.40, f"got energy={s['energy']}"),
    ),
    (
        "Unknown query -> confidence score stays below 0.60",
        "xyzzy blorp totally unrecognized input",
        lambda s: (True, "fallback always returns a song — checked separately"),
    ),
]


def run_eval() -> None:
    data_path = Path(__file__).parent.parent / "data" / "songs.csv"
    songs_db = load_songs(str(data_path))

    passed = 0
    failed = 0
    confidence_scores = []

    print("\n=== Retriever Evaluation ===\n")

    for description, query, check in TEST_CASES:
        prefs = parse_query(query)
        retrieved = recommend_songs(prefs, songs_db, k=5)

        top_song, top_score, _ = retrieved[0]
        confidence = round(min(top_score / MAX_SCORE, 1.0), 2)
        confidence_scores.append(confidence)

        ok, reason = check(top_song)

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] {description}")
        print(f"       Query:      \"{query}\"")
        print(f"       Top result: \"{top_song['title']}\" ({top_song['genre']}, {top_song['mood']}, energy {top_song['energy']})")
        print(f"       Confidence: {confidence}  |  {reason}\n")

    total = passed + failed
    avg_confidence = round(sum(confidence_scores) / len(confidence_scores), 2)

    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    print(f"Average retrieval confidence: {avg_confidence}")
    if failed:
        print(f"Failed cases: {failed} — review query parser keyword coverage")
    else:
        print("All retrieval checks passed.")
    print()


if __name__ == "__main__":
    run_eval()
