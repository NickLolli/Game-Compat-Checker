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
    # NVIDIA RTX 40-series (incl. Super refresh)
    "rtx 4090": 39000,
    "rtx 4080 super": 34000,
    "rtx 4080": 32000,
    "rtx 4070 ti super": 29500,
    "rtx 4070 ti": 27500,
    "rtx 4070 super": 25000,
    "rtx 4070": 22500,
    "rtx 4060 ti": 17500,
    "rtx 4060": 15500,
    "rtx 4050": 11500,
    # NVIDIA RTX 30-series
    "rtx 3090 ti": 27500,
    "rtx 3090": 26000,
    "rtx 3080 ti": 25000,
    "rtx 3080": 24000,
    "rtx 3070 ti": 20500,
    "rtx 3070": 19500,
    "rtx 3060 ti": 17000,
    "rtx 3060": 14500,
    "rtx 3050 ti": 11000,
    "rtx 3050": 10500,
    # NVIDIA RTX 20-series
    "rtx 2080 ti": 18500,
    "rtx 2080 super": 16500,
    "rtx 2080": 15500,
    "rtx 2070 super": 14500,
    "rtx 2070": 13500,
    "rtx 2060 super": 12500,
    "rtx 2060": 11500,
    # NVIDIA GTX 16-series
    "gtx 1660 ti": 10500,
    "gtx 1660 super": 9800,
    "gtx 1660": 9200,
    "gtx 1650 super": 7800,
    "gtx 1650": 6200,
    # NVIDIA GTX 10-series
    "gtx 1080 ti": 13500,
    "gtx 1080": 11000,
    "gtx 1070 ti": 10200,
    "gtx 1070": 9500,
    "gtx 1060 6gb": 7500,
    "gtx 1060": 7500,
    "gtx 1050 ti": 4700,
    "gtx 1050": 3800,
    # NVIDIA GTX 900-series and older (still referenced by older games)
    "gtx 980 ti": 9800,
    "gtx 980": 8000,
    "gtx 970": 7000,
    "gtx 960": 4900,
    "gtx 950": 3900,
    "gtx 750 ti": 2900,
    "gt 1030": 1900,
    # AMD Radeon RX 7000-series
    "rx 7900 xtx": 33000,
    "rx 7900 xt": 29500,
    "rx 7900 gre": 27000,
    "rx 7800 xt": 24000,
    "rx 7700 xt": 20500,
    "rx 7600 xt": 15500,
    "rx 7600": 14000,
    # AMD Radeon RX 6000-series
    "rx 6950 xt": 25500,
    "rx 6900 xt": 24500,
    "rx 6800 xt": 22500,
    "rx 6800": 20500,
    "rx 6750 xt": 19500,
    "rx 6700 xt": 18500,
    "rx 6650 xt": 15000,
    "rx 6600 xt": 13500,
    "rx 6600": 12500,
    "rx 6500 xt": 8500,
    "rx 6400": 6500,
    # AMD Radeon RX 5000-series and older
    "rx 5700 xt": 12000,
    "rx 5700": 10800,
    "rx 5600 xt": 10000,
    "rx 5500 xt": 7800,
    "rx 590": 7000,
    "rx 580": 6500,
    "rx 570": 5800,
    "rx 480": 6000,
    "rx 470": 5500,
    # Intel Arc discrete
    "arc a770": 14500,
    "arc a750": 13000,
    "arc a580": 11500,
    "arc a380": 6000,
    # Integrated graphics (rough estimates - these vary a lot by
    # power/thermal limits, so treat as "typical laptop" numbers)
    "arc graphics": 3500,          # Intel Core Ultra iGPU (your laptop)
    "iris xe graphics": 2200,      # Intel 11th/12th gen iGPU
    "uhd graphics": 900,           # Older Intel iGPU
    "radeon graphics": 2800,       # AMD Ryzen iGPU (varies by chip)
    "radeon 780m": 4200,           # Newer AMD APU iGPU
    "radeon 680m": 3400,
    "vega 8": 1600,                # Older AMD Ryzen APU iGPU
    "vega 11": 1900,
}

CPU_SCORES: dict[str, int] = {
    # Intel Core Ultra (laptop, current gen)
    "core ultra 9 185h": 34000,
    "core ultra 7 165h": 30000,
    "core ultra 7 155h": 28500,   # your laptop
    "core ultra 5 135h": 25000,
    "core ultra 5 125h": 24000,
    # Intel Core 13th/14th gen (desktop)
    "core i9-14900k": 63000,
    "core i7-14700k": 53000,
    "core i5-14600k": 42000,
    "core i5-14400f": 32000,
    "core i9-13900k": 60000,
    "core i7-13700k": 49000,
    "core i5-13600k": 40000,
    "core i5-13400f": 30000,
    # Intel Core 12th gen
    "core i9-12900k": 54000,
    "core i7-12700k": 45000,
    "core i5-12600k": 36000,
    "core i5-12400f": 24000,
    "core i5-12400": 23500,
    "core i3-12100": 15500,
    # Intel Core 11th gen and older desktop
    "core i9-11900k": 38000,
    "core i7-11700k": 33000,
    "core i5-11600k": 27000,
    "core i7-10700k": 30000,
    "core i5-10600k": 24500,
    "core i5-10400f": 19500,
    "core i7-9700k": 20000,
    "core i5-9400f": 13000,
    "core i7-8700k": 19500,
    "core i5-8400": 13500,
    "core i7-7700k": 15500,
    "core i5-7600k": 11500,
    "core i5-7500": 10800,
    "core i5-7400": 10200,
    "core i3-7100": 8000,
    "core i7-6700k": 13500,
    "core i5-6600k": 10500,
    # Old Nehalem/Sandy-era Core i-series (still show up in older game
    # requirements, e.g. Counter-Strike 2's Core i5 750)
    "core i5 750": 3300,
    "core i7 920": 3500,
    "core i5-2500k": 6500,
    "core i7-2600k": 7500,
    "core i5-3570k": 7200,
    "core i7-4770k": 8500,
    # Budget Intel (Pentium/Celeron - very common minimum-spec CPUs)
    "pentium g4560": 4200,
    "pentium gold g6400": 5500,
    "celeron g5905": 4400,
    # AMD Ryzen 9000/7000-series (desktop)
    "ryzen 9 9950x": 65000,
    "ryzen 7 9700x": 48000,
    "ryzen 9 7950x3d": 62000,
    "ryzen 9 7950x": 60000,
    "ryzen 9 7900x": 55000,
    "ryzen 7 7800x3d": 42000,
    "ryzen 7 7700x": 44000,
    "ryzen 5 7600x": 35000,
    "ryzen 5 7600": 33500,
    # AMD Ryzen 5000-series
    "ryzen 9 5950x": 46000,
    "ryzen 9 5900x": 42000,
    "ryzen 7 5800x3d": 32000,
    "ryzen 7 5800x": 34000,
    "ryzen 5 5600x": 25000,
    "ryzen 5 5600": 24000,
    "ryzen 5 5500": 21000,
    # AMD Ryzen 3000-series and older
    "ryzen 9 3900x": 33000,
    "ryzen 7 3700x": 24500,
    "ryzen 5 3600x": 19500,
    "ryzen 5 3600": 18000,
    "ryzen 3 3300x": 15000,
    "ryzen 5 2600": 13000,
    "ryzen 5 1600": 11500,
    "fx-8350": 4800,               # older AMD FX-series, still referenced by some games
    "fx-6300": 3400,
    "athlon 200ge": 3900,
    # AMD Ryzen mobile (laptop, current-ish gen)
    "ryzen 9 7940hs": 33000,
    "ryzen 7 7840hs": 31000,
    "ryzen 7 7735hs": 27500,
    "ryzen 5 7640hs": 26000,
    "ryzen 7 6800h": 24500,
    "ryzen 5 6600h": 21000,
    "ryzen 7 5800h": 22000,
    "ryzen 5 5600h": 18500,
}


# ---------------------------------------------------------------
# Normalization + fuzzy matching
# ---------------------------------------------------------------

_NOISE_WORDS = [
    r"\(r\)", r"\(tm\)", r"\(c\)",
    "™", "®", "©",   # Steam uses actual Unicode trademark symbols, not just (TM)/(R) text
    "intel", "amd", "nvidia", "geforce", "gforce", "radeon",  # "gforce" is a common typo for "geforce" seen in real game listings
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


def find_score(raw_name: str | None, table: dict[str, int], cutoff: float = 0.6) -> tuple[int | None, str | None]:
    """
    Look up a benchmark score for a raw hardware name against a table.
    Returns (score, matched_key) or (None, None) if nothing close enough
    was found. Tries exact match first, then fuzzy matching.

    raw_name can legitimately be None - happens when steam.py's parser
    couldn't extract a given field (e.g. a game with no "recommended"
    tier listed at all, or oddly formatted requirements text) - treat
    that the same as "no match found" rather than crashing.
    """
    if not raw_name:
        return None, None

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
# Display formatting - for autocomplete suggestions in the manual
# entry form. Table keys are lowercase normalized ("rtx 3060", "core
# i5-8400"), which isn't how you'd want to see them in a dropdown.
# This isn't perfect (acronym detection is a fixed list, not
# exhaustive), but it's good enough for a readable suggestion list.
# ---------------------------------------------------------------

_ACRONYMS = {"rtx", "gtx", "rx", "xt", "ti", "amd", "fx"}
_INTEL_TIER_PATTERN = re.compile(r"^i[3579](-.*)?$")  # i5, i7-8400, etc. - Intel keeps these lowercase


def _format_display_name(key: str) -> str:
    words = []
    for word in key.split():
        if word in _ACRONYMS:
            words.append(word.upper())
        elif word.startswith("fx-"):
            words.append("FX-" + word[3:])  # "fx-6300" -> "FX-6300"
        elif _INTEL_TIER_PATTERN.match(word):
            words.append(word)  # keep "i5", "i7-8400" lowercase as Intel brands it
        elif word.endswith("gb"):
            words.append(word[:-2] + "GB")
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


# Brand prefixes for readability in the autocomplete dropdown (e.g.
# "GTX 1060" -> "NVIDIA GTX 1060"). Matched against the raw lowercase
# key's start, checked in order (more specific patterns first). This
# is purely cosmetic - find_score()'s normalizer strips these same
# vendor words back out before matching, so it doesn't affect scoring.
_GPU_BRAND_PREFIXES = [
    ("rtx", "NVIDIA"),
    ("gtx", "NVIDIA"),
    ("gt ", "NVIDIA"),
    ("arc", "Intel"),
    ("iris", "Intel"),
    ("uhd", "Intel"),
    ("radeon", "AMD"),   # covers "radeon graphics", "radeon 780m" etc.
    ("rx ", "AMD Radeon"),
    ("vega", "AMD Radeon"),
]

_CPU_BRAND_PREFIXES = [
    ("core ultra", "Intel"),
    ("core i", "Intel"),
    ("core ", "Intel"),   # older "Core i5 750"-style entries without a dash
    ("pentium", "Intel"),
    ("celeron", "Intel"),
    ("ryzen", "AMD"),
    ("fx-", "AMD"),
    ("athlon", "AMD"),
]


def _add_brand_prefix(key: str, formatted: str, brand_rules: list[tuple[str, str]]) -> str:
    for prefix, brand in brand_rules:
        if key.startswith(prefix):
            return f"{brand} {formatted}"
    return formatted


def list_cpu_options() -> list[str]:
    """All known CPU names, nicely formatted with brand prefix and
    alphabetically sorted - used to power autocomplete in the manual
    entry form."""
    names = [
        _add_brand_prefix(k, _format_display_name(k), _CPU_BRAND_PREFIXES)
        for k in CPU_SCORES
    ]
    return sorted(names)


def list_gpu_options() -> list[str]:
    """All known GPU names, nicely formatted with brand prefix and
    alphabetically sorted - used to power autocomplete in the manual
    entry form."""
    names = [
        _add_brand_prefix(k, _format_display_name(k), _GPU_BRAND_PREFIXES)
        for k in GPU_SCORES
    ]
    return sorted(names)


# ---------------------------------------------------------------
# TODO (future improvement): replace/supplement this hardcoded table
# with a larger dataset - e.g. download a public PassMark CPU/GPU
# CSV export periodically and merge it in, so new hardware releases
# don't require manually editing this file forever.
# ---------------------------------------------------------------