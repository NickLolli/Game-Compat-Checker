"""
End-to-end demo: ties hardware.py + steam.py + scoring.py together.

Usage:
    python -m app.check_game "Cyberpunk 2077"
    python -m app.check_game "Call of Duty"

This is a temporary CLI test harness - Week 4 replaces this with
proper FastAPI endpoints, but it's useful right now to confirm the
full pipeline works before building the API layer.
"""

import json
import sys

from app.hardware import detect_hardware
from app.steam import search_game, get_game_requirements
from app.scoring import compare_specs


def check_game(query: str):
    print(f"Searching Steam for: {query}\n")
    results = search_game(query)
    if not results:
        print("No matches found.")
        return

    print("Matches:")
    for r in results:
        print(f"  {r['appid']}: {r['name']}")

    top = results[0]
    print(f"\nUsing: {top['name']} ({top['appid']})\n")

    requirements = get_game_requirements(top["appid"])
    print("Parsed requirements:")
    print(json.dumps(requirements, indent=2))

    print("\nDetecting your hardware...")
    user_specs = detect_hardware()
    print(json.dumps(user_specs, indent=2))

    print("\nVerdict:")
    verdict = compare_specs(user_specs, requirements)
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Cyberpunk 2077"
    check_game(query)