"""
AI-powered music recommender using Gemini + RAG.
Flow: user query → keyword parser → song retriever → Gemini → response + log
"""

import os
import sys
import json
import logging
from pathlib import Path

from google import genai

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).parent))
from recommender import load_songs, recommend_songs

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


# ── Main chat loop ────────────────────────────────────────────────────────────

def run_chat() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Set it with:  export GEMINI_API_KEY=your_key_here")
        sys.exit(1)

    data_path = Path(__file__).parent.parent / "data" / "songs.csv"
    songs_db = load_songs(str(data_path))

    client = genai.Client(api_key=api_key)

    print("\n=== Music Recommender — Gemini + RAG ===")
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

        # Generation step: send retrieved songs + query to Gemini
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

        # Log query, retrieved songs, and response
        logging.info(json.dumps({
            "query": user_input,
            "parsed_prefs": prefs,
            "retrieved_songs": [s["title"] for s, _, _ in retrieved],
            "response_preview": reply[:120],
        }))
