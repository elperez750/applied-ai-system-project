"""
AI-powered music recommender using Gemini + RAG.
Flow: user query → keyword parser → song retriever → Gemini → response + log
"""

import os
import sys
import json
import logging
from pathlib import Path

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).parent))
from src.recommender import load_songs, recommend_songs

# ── Logging setup ─────────────────────────────────────────────────────────────

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / "recommender.log"),
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── Keyword maps for query parsing ────────────────────────────────────────────

GENRE_KEYWORDS: dict[str, list[str]] = {
    "pop":        ["pop", "mainstream", "catchy"],
    "lofi":       ["lofi", "lo-fi", "lo fi"],
    "rock":       ["rock", "guitar", "band"],
    "ambient":    ["ambient", "atmospheric", "space"],
    "jazz":       ["jazz", "coffee shop", "smooth"],
    "synthwave":  ["synthwave", "retro", "80s", "neon"],
    "electronic": ["electronic", "edm", "dance", "club"],
    "indie pop":  ["indie"],
    "country":    ["country", "western"],
    "acoustic":   ["acoustic", "unplugged"],
    "r&b":        ["r&b", "rnb", "soul"],
    "hip-hop":    ["hip-hop", "hip hop", "rap"],
}

MOOD_KEYWORDS: dict[str, list[str]] = {
    "happy":   ["happy", "upbeat", "joyful", "cheerful", "fun", "good vibes"],
    "chill":   ["chill", "calm", "easy", "mellow", "relax", "lazy"],
    "intense": ["intense", "powerful", "hype", "pump", "aggressive"],
    "moody":   ["moody", "dark", "melancholic", "sad", "gloomy", "rainy", "heartbreak"],
    "relaxed": ["relaxed", "laid back", "peaceful", "gentle", "slow"],
    "focused": ["focus", "study", "concentrate", "work", "productive", "coding"],
}

HIGH_ENERGY_WORDS = {"high energy", "intense", "pump", "hype", "workout", "gym", "run", "fast"}
LOW_ENERGY_WORDS  = {"low energy", "slow", "quiet", "soft", "gentle", "sleepy", "wind down"}


# ── Query parser ──────────────────────────────────────────────────────────────

def parse_query(query: str) -> dict:
    """Extract structured preferences from a natural language query via keyword matching."""
    q = query.lower()
    prefs: dict = {"genre": None, "mood": None, "energy": 0.5, "likes_acoustic": False}

    for genre, keywords in GENRE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            prefs["genre"] = genre
            break

    for mood, keywords in MOOD_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            prefs["mood"] = mood
            break

    if any(w in q for w in HIGH_ENERGY_WORDS):
        prefs["energy"] = 0.9
    elif any(w in q for w in LOW_ENERGY_WORDS):
        prefs["energy"] = 0.25

    if "acoustic" in q or "unplugged" in q:
        prefs["likes_acoustic"] = True

    return prefs


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(user_query: str, retrieved: list) -> str:
    song_lines = "\n".join(
        f"- \"{s['title']}\" by {s['artist']} "
        f"(genre: {s['genre']}, mood: {s['mood']}, energy: {s['energy']:.2f})"
        for s, _, _ in retrieved
    )
    return (
        f"You are a warm, knowledgeable music recommendation assistant.\n\n"
        f"The user said: \"{user_query}\"\n\n"
        f"Here are the top songs retrieved from the catalog that best match their request:\n"
        f"{song_lines}\n\n"
        f"Write a friendly, conversational recommendation. Mention each song by name and "
        f"give a one-sentence reason why it fits. Keep your reply under 150 words."
    )


# ── Demo mode (no API key needed) ────────────────────────────────────────────

def _demo_reply(retrieved: list, user_query: str) -> str:
    """Generate a realistic response from retrieved songs without calling the API."""
    songs = [s for s, _, _ in retrieved]
    names = ", ".join(f'"{s["title"]}" by {s["artist"]}' for s in songs[:3])
    top = songs[0]
    return (
        f'Based on your request for "{user_query}", here are my top picks from the catalog. '
        f'{names} all fit the vibe well. '
        f'"{top["title"]}" by {top["artist"]} is the strongest match — '
        f'it\'s {top["genre"]}, {top["mood"]}, with an energy level of {top["energy"]:.2f}. '
        f'Give it a listen and let me know if you want something different!'
    )


# ── Main chat loop ────────────────────────────────────────────────────────────

def run_chat(demo: bool = False) -> None:
    client = None
    if not demo:
        from google import genai  # lazy import so tests can import parse_query without the package
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable is not set.")
            print("Tip: run with --demo to try the system without an API key.")
            sys.exit(1)
        client = genai.Client(api_key=api_key)

    data_path = Path(__file__).parent.parent / "data" / "songs.csv"
    songs_db = load_songs(str(data_path))

    mode_label = "[DEMO MODE — responses are template-based]" if demo else "[Gemini 2.0 Flash]"
    print(f"\n=== Music Recommender — Gemini + RAG  {mode_label} ===")
    print("Tell me what you're in the mood for. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        # RAG step: parse query and retrieve matching songs
        prefs = parse_query(user_input)
        retrieved = recommend_songs(prefs, songs_db, k=5)

        # Confidence score: normalize top song's raw score against the max possible (4.5)
        top_score = retrieved[0][1] if retrieved else 0.0
        confidence = round(min(top_score / 4.5, 1.0), 2)

        if confidence < 0.4:
            print(f"\n[Low confidence: {confidence:.2f} — no close catalog match found, results may be off]\n")

        # Generation step
        if demo:
            reply = _demo_reply(retrieved, user_input)
        else:
            prompt = build_prompt(user_input, retrieved)
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                reply = response.text.strip()
            except Exception as exc:
                reply = f"[Gemini error: {exc}]"
                logging.error("Gemini API error: %s", exc)

        print(f"\nAssistant: {reply}\n")

        # Log query, retrieved songs, confidence, and response
        logging.info(json.dumps({
            "query": user_input,
            "parsed_prefs": prefs,
            "confidence": confidence,
            "retrieved_songs": [s["title"] for s, _, _ in retrieved],
            "response_preview": reply[:120],
        }))
