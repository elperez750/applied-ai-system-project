"""
Entry point for the AI Music Recommender.
Run with: python -m src.main
Demo mode (no API key): python -m src.main --demo
"""

import sys
from src.chat import run_chat

if __name__ == "__main__":
    run_chat(demo="--demo" in sys.argv)
