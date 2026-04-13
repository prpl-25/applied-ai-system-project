"""
Command line runner for the Music Recommender Simulation.

Usage:
  python src/main.py            # Classic mode: run scoring-based recommendations
  python src/main.py --ai       # AI mode: conversational RAG + agentic workflow
                                 # (requires ANTHROPIC_API_KEY environment variable)

Classic mode implements the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse
import logging
import os

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 
    print(f"Loaded {len(songs)} songs from the dataset.")  
    user_profiles = {
        "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9},
        "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.3},
        "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.85},
    }

    for profile_name, user_prefs in user_profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("\n" + "="*60)
        print(f"TOP MUSIC RECOMMENDATIONS: {profile_name}")
        print("="*60 + "\n")

        for i, rec in enumerate(recommendations, 1):
            song, score, explanation = rec
            print(f"{i}. {song['title']}")
            print(f"   Score: {score:.2f}/6")
            print(f"   Why: {explanation}")
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Music Recommender")
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Launch conversational AI mode (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    if args.ai:
        try:
            import anthropic
            from ai_recommender import run_ai_session
        except ImportError:
            print("ERROR: anthropic package not installed. Run: pip install anthropic")
            raise SystemExit(1)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
            raise SystemExit(1)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler("ai_recommender.log"),
                logging.StreamHandler(),
            ],
        )

        songs = load_songs("data/songs.csv")
        client = anthropic.Anthropic(api_key=api_key)
        run_ai_session(songs, client)
    else:
        main()
