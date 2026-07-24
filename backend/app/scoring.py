"""
Week 2 TODO: comparison / verdict logic.

Plan:
- Normalize a detected or user-entered GPU/CPU name to a benchmark score
  using benchmarks.py's lookup table.
- Normalize a game's parsed min/recommended requirements the same way.
- Compare ratios (user_score / required_score) to produce a verdict:
    >= 1.1x recommended -> "Very good"
    >= 1.0x recommended -> "Good"
    >= 1.0x minimum      -> "Playable (lower settings)"
    <  1.0x minimum      -> "Unplayable"
- Whichever component (CPU/GPU/RAM) has the lowest ratio is the
  suggested upgrade target.
"""

# Placeholder - implement in Week 2
def compare_specs(user_specs: dict, game_requirements: dict) -> dict:
    raise NotImplementedError("Week 2: build the scoring/verdict logic here")
