"""
Week 2: CPU/GPU name -> benchmark score lookup table, with fuzzy
name matching since hardware names never match exactly between
sources (detected hardware, Steam requirement text, this table).

Scores are rough relative-performance numbers on a single scale per
component type (loosely PassMark-style: bigger = faster). They are
NOT precise - the goal is "which of these two is roughly better and
by how much," not scientific benchmarking. Good enough for a verdict
like "Good/Playable/Unplayable," not good enough for exact FPS
prediction.

MAINTENANCE NOTE: this table needs to grow over time as new hardware
releases. Consider later replacing/supplementing this hardcoded dict
with a scraped or downloaded public benchmark dataset (e.g. a
PassMark or Geekbench export) - see TODO at the bottom of the file.
"""

import re
from difflib import get_close_matches

# ---------------------------------------------------------------
# Lookup tables. Keys are normalized (see normalize_name below):
# lowercase, no vendor/trademark noise, collapsed whitespace.
# ---------------------------------------------------------------

GPU_SCORES: dict[str, int] = {
    # NVIDIA RTX 40-series
    "rtx 4090": 39000,
    "rtx 4080": 32000,
    "rtx 4070 ti": 27500,
    "rtx 4070": 22500,
    "rtx 4060 ti": 17500,
    "rtx 4060": 15500,
    # NVIDIA RTX 30-series
    "rtx 3090": 26000,
    "rtx 3080": 24000,
    "rtx 3070": 19500,
    "rtx 3060 ti": 17000,
    "rtx 3060": 14500,
    "rtx 3050": 10500,
    # NVIDIA GTX 16-series / older
    "gtx 1660 ti": 10500,
    "gtx 1660 super": 9800,
    "gtx 1660": 9200,
    "gtx 1650 super": 7800,
    "gtx 1650": 6200,
    "gtx 1080 ti": 13500,
    "gtx 1080": 11000,
    "gtx 1070": 9500,
    "gtx 1060": 7500,
    "gtx 1050 ti": 4700,
    "gtx 1050": 3800,
    # AMD Radeon RX
    "rx 7900 xtx": 33000,
    "rx 7900 xt": 29500,
    "rx 7800 xt": 24000,
    "rx 7700 xt": 20500,
    "rx 7600": 14000,
    "rx 6800 xt": 22500,
    "rx 6700 xt": 18500,
    "rx 6600": 12500,
    "rx 6600 xt": 13500,
    "rx 5700 xt": 12000,
    "rx 580": 6500,
    "rx 570": 5800,
    # Integrated graphics (rough estimates - these vary a lot by
    # power/thermal limits, so treat as "typical laptop" numbers)
    "arc graphics": 3500,          # Intel Core Ultra iGPU (your laptop)
    "iris xe graphics": 2200,      # Intel 11th/12th gen iGPU
    "uhd graphics": 900,           # Older Intel iGPU
    "radeon graphics": 2800,       # AMD Ryzen iGPU (varies by chip)
    "radeon 780m": 4200,           # Newer AMD APU iGPU
}

CPU_SCORES: dict[str, int] = {
    # Intel Core Ultra (laptop, current gen)
    "core ultra 9 185h": 34000,
    "core ultra 7 165h": 30000,
    "core ultra 7 155h": 28500,   # your laptop
    "core ultra 5 125h": 24000,
    # Intel Core 13th/14th gen (desktop)
    "core i9-14900k": 63000,
    "core i7-14700k": 53000,
    "core i5-14600k": 42000,
    "core i9-13900k": 60000,
    "core i7-13700k": 49000,
    "core i5-13600k": 40000,
    "core i5-12400f": 24000,
    "core i5-12400": 23500,
    "core i3-12100": 15500,
    # AMD Ryzen 7000-series
    "ryzen 9 7950x3d": 62000,
    "ryzen 9 7900x": 55000,
    "ryzen 7 7800x3d": 42000,
    "ryzen 7 7700x": 44000,
    "ryzen 5 7600x": 35000,
    # AMD Ryzen 5000-series
    "ryzen 9 5950x": 46000,
    "ryzen 7 5800x3d": 32000,
    "ryzen 7 5800x": 34000,
    "ryzen 5 5600x": 25000,
    "ryzen 5 5600": 24000,
    # Older / budget
    "core i7-9700k": 20000,
    "core i5-9400f": 13000,
    "ryzen 5 3600": 18000,
    "ryzen 3 3300x": 15000,
}


# ---------------------------------------------------------------
# Normalization + fuzzy matching
# ---------------------------------------------------------------

_NOISE_WORDS = [
    r"\(r\)", r"\(tm\)", r"\(c\)",
    "intel", "amd", "nvidia", "geforce", "radeon",
    "processor", "graphics card", "cpu", "gpu",
    "with", "family",
]


def normalize_name(raw_name: str) -> str:
    """Lowercase, strip vendor/trademark noise, collapse whitespace.
    e.g. 'Intel(R) Core(TM) Ultra 7 155H' -> 'core ultra 7 155h'
    """
    name = raw_name.lower()
    for word in _NOISE_WORDS:
        name = re.sub(word, "", name)
    name = re.sub(r"[^\w\s]", " ", name)   # strip remaining punctuation
    name = re.sub(r"\s+", " ", name).strip()
    return name


def find_score(raw_name: str, table: dict[str, int], cutoff: float = 0.6) -> tuple[int | None, str | None]:
    """
    Look up a benchmark score for a raw hardware name against a table.
    Returns (score, matched_key) or (None, None) if nothing close enough
    was found. Tries exact match first, then fuzzy matching.
    """
    normalized = normalize_name(raw_name)

    if normalized in table:
        return table[normalized], normalized

    # Fuzzy fallback: find the closest key by string similarity.
    # Useful when e.g. detected name has extra words the table doesn't
    # ("rtx 3060 laptop gpu" vs table's "rtx 3060").
    matches = get_close_matches(normalized, table.keys(), n=1, cutoff=cutoff)
    if matches:
        return table[matches[0]], matches[0]

    # Last resort: substring containment either direction, since
    # difflib similarity can fail on strings of very different length
    # (e.g. "rtx 3060" is a clean substring of "rtx 3060 laptop gpu"
    # but difflib may not rate them as similar enough).
    for key in table:
        if key in normalized or normalized in key:
            return table[key], key

    return None, None


# ---------------------------------------------------------------
# TODO (future improvement): replace/supplement this hardcoded table
# with a larger dataset - e.g. download a public PassMark CPU/GPU
# CSV export periodically and merge it in, so new hardware releases
# don't require manually editing this file forever.
# ---------------------------------------------------------------