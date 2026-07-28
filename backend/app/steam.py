"""
Week 3: Steam data pipeline.

Two jobs:
1. search_game(name) - find a Steam App ID from a typed game name.
2. get_game_requirements(appid) - fetch + parse that game's min/recommended
   requirements into the clean shape scoring.py expects:

   {
       "minimum":     {"cpu": "...", "gpu": "...", "ram_gb": 8},
       "recommended": {"cpu": "...", "gpu": "...", "ram_gb": 16},
   }

IMPORTANT CAVEAT: Steam does not enforce a standard format for requirements
text - some games list "Processor", others "CPU"; some give exact RAM ("8 GB
RAM"), others a range or nothing at all. The parser below uses keyword +
regex matching to be as forgiving as possible, but it WILL occasionally
fail to extract a field cleanly for weirdly-formatted games. When that
happens it returns None for that field rather than guessing - scoring.py
already handles None gracefully (reports it as "unmatched").
"""

import re
import requests
from bs4 import BeautifulSoup

STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


# ---------------------------------------------------------------
# Step 1: find a game's App ID from a typed name
# ---------------------------------------------------------------

def _is_base_game(appid: int) -> bool:
    """Steam's search endpoint doesn't reliably distinguish games from
    DLC (its 'type' field is just 'app' for everything). The
    appdetails endpoint DOES have an accurate type field ('game',
    'dlc', 'demo', 'music', etc.) - filters=basic keeps the response
    small since we only need this one field, not full store data."""
    try:
        resp = requests.get(
            APPDETAILS_URL,
            params={"appids": appid, "cc": "us", "l": "english", "filters": "basic"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        app_data = data.get(str(appid), {})
        return app_data.get("success") and app_data.get("data", {}).get("type") == "game"
    except requests.exceptions.RequestException:
        # If this one lookup fails, don't let it break the whole
        # search - just exclude the candidate rather than crashing.
        return False


def search_game(name: str, max_results: int = 5) -> list[dict]:
    """Returns a list of {"appid": int, "name": str} candidates.
    The caller (or the user, if there are multiple matches) should
    pick the right one - e.g. searching "Doom" returns several games.

    Only returns base games - Steam's search also matches DLC, demos,
    soundtracks, and other non-game content (e.g. searching "Destiny
    2" returns its expansions too). We fetch extra raw candidates and
    check each one's real type via appdetails, since the search
    endpoint's own type field isn't reliable for this (see
    _is_base_game). This costs one extra request per candidate
    checked, so it's slower than a single search call - acceptable
    for a local dev tool, but worth knowing about.
    """
    resp = requests.get(
        STORE_SEARCH_URL,
        params={"term": name, "cc": "us", "l": "english"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("items", [])

    games = []
    for item in candidates:
        if _is_base_game(item["id"]):
            games.append({"appid": item["id"], "name": item["name"]})
        if len(games) >= max_results:
            break

    return games


# ---------------------------------------------------------------
# Step 2: fetch raw requirements HTML for a specific App ID
# ---------------------------------------------------------------

def fetch_raw_requirements(appid: int) -> dict:
    """Returns Steam's raw pc_requirements block:
    {"minimum": "<html>...", "recommended": "<html>..."}
    Some games only have "minimum" and no "recommended", or vice versa.

    Raises ValueError with a clear message for known failure cases
    (delisted/region-locked app, or a game with no PC requirements
    listed at all) rather than letting a confusing exception bubble up.
    """
    resp = requests.get(
        APPDETAILS_URL, params={"appids": appid, "cc": "us", "l": "english"}, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()

    app_data = data.get(str(appid), {})
    if not app_data.get("success"):
        # Happens for delisted, region-locked, or otherwise
        # unavailable app IDs - Steam just says success: false with
        # no further detail.
        raise ValueError(
            f"Steam has no page data for appid {appid} "
            f"(it may be delisted or unavailable in this region)"
        )

    pc_requirements = app_data.get("data", {}).get("pc_requirements", {})

    # Known Steam API quirk: when a game genuinely has no PC
    # requirements listed, Steam returns an empty LIST [] instead of
    # an empty dict {} for this field - breaks .get() calls downstream
    # if we don't normalize it here.
    if not isinstance(pc_requirements, dict):
        pc_requirements = {}

    if not pc_requirements.get("minimum") and not pc_requirements.get("recommended"):
        raise ValueError(
            f"'{app_data.get('data', {}).get('name', appid)}' doesn't list "
            f"PC system requirements on its Steam page"
        )

    return pc_requirements


# ---------------------------------------------------------------
# Step 3: parse the messy HTML into clean {cpu, gpu, ram_gb}
# ---------------------------------------------------------------

# Steam's requirement lines use varying labels for the same thing -
# try each of these, in order, for a given field.
_CPU_LABELS = ["processor", "cpu"]
_GPU_LABELS = ["graphics", "video card", "gpu"]
_RAM_LABELS = ["memory", "ram"]
_OS_LABELS = ["os", "operating system"]
_DIRECTX_LABELS = ["directx"]
_STORAGE_LABELS = ["storage", "hard drive space", "hard drive", "disk space"]


def _extract_list_items(html: str) -> list[str]:
    """Steam wraps each requirement line in <li>Label: value</li>.
    Returns the plain-text content of each <li>, e.g.
    ["OS: Windows 10", "Processor: Intel Core i5-8400", ...]
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    return [li.get_text(separator=" ", strip=True) for li in soup.find_all("li")]


def _find_field(lines: list[str], labels: list[str]) -> str | None:
    """Find the first line whose label matches one of `labels`
    (case-insensitive), and return the value after the colon."""
    for line in lines:
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        if label.strip().lower() in labels:
            return value.strip()
    return None


def _extract_ram_gb(ram_text: str | None) -> float | None:
    """Steam RAM text looks like '8 GB RAM' or '16 GB' or sometimes a
    range like '8 GB or more'. Pull out the first number we find."""
    if not ram_text:
        return None
    match = re.search(r"(\d+(\.\d+)?)\s*GB", ram_text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _strip_descriptive_prefix(text: str | None) -> str | None:
    """Some games prefix the actual hardware name with a description,
    separated by ' - ' (space-dash-space, distinct from a hyphenated
    model number like 'i5-8400' which has no spaces around its dash).
    e.g. Counter-Strike 2 lists CPU as '4 hardware CPU threads -
    Intel Core i5 750' - we want just 'Intel Core i5 750'. If there's
    no ' - ' separator, returns the text unchanged."""
    if not text or " - " not in text:
        return text
    return text.rsplit(" - ", 1)[-1].strip()


def _strip_trailing_annotations(text: str | None) -> str | None:
    """Some games append extra info after the hardware name that
    breaks matching: a clock speed after '@' ('Core i5-7400 CPU @
    3.00GHz') and/or a semicolon-separated note ('... ; Shader Model
    5'). Strip both, keeping just the hardware name itself."""
    if not text:
        return text
    text = text.split(";", 1)[0]
    text = text.split("@", 1)[0]
    return text.strip()


def _first_alternative(text: str | None) -> str | None:
    """Steam lists alternatives two different ways depending on the
    game: 'Intel i5-8400 or AMD Ryzen 5 2600' AND 'AMD RX 470, NVIDIA
    GTX 970 / 1060'. The benchmark matcher expects a single hardware
    name, so split on whichever separator appears first and take just
    the first option. (Future improvement: try matching all
    alternatives and use whichever scores higher, since any of them
    would satisfy the requirement - first-option is a simplification.)
    """
    if not text:
        return None
    # Split on "or" or "," - whichever comes first in the string -
    # so we don't accidentally split on a comma that appears AFTER
    # an "or" split point (e.g. only take the true first option).
    or_split = re.split(r"\s+or\s+", text, maxsplit=1, flags=re.IGNORECASE)
    comma_split = text.split(",", 1)

    if len(or_split) > 1 and (len(comma_split) == 1 or len(or_split[0]) <= len(comma_split[0])):
        first = or_split[0]
    else:
        first = comma_split[0]

    return first.strip()


def _parse_tier(html: str) -> dict:
    """Parse one tier (minimum or recommended) into a dict.
    cpu/gpu/ram_gb are used for actual scoring (scoring.py compares
    these against detected hardware). os/directx/storage are
    reference-only info we display but don't compare - we don't
    detect the user's free disk space or exact Windows build number,
    so there's nothing meaningful to score them against."""
    lines = _extract_list_items(html)
    return {
        "cpu": _first_alternative(_strip_descriptive_prefix(_strip_trailing_annotations(_find_field(lines, _CPU_LABELS)))),
        "gpu": _first_alternative(_strip_descriptive_prefix(_strip_trailing_annotations(_find_field(lines, _GPU_LABELS)))),
        "ram_gb": _extract_ram_gb(_find_field(lines, _RAM_LABELS)),
        "os": _find_field(lines, _OS_LABELS),
        "directx": _find_field(lines, _DIRECTX_LABELS),
        "storage": _find_field(lines, _STORAGE_LABELS),
    }


def parse_requirements(raw_requirements: dict) -> dict:
    return {
        "minimum": _parse_tier(raw_requirements.get("minimum", "")),
        "recommended": _parse_tier(raw_requirements.get("recommended", "")),
    }


# ---------------------------------------------------------------
# Convenience: do it all in one call
# ---------------------------------------------------------------

def get_game_requirements(appid: int) -> dict:
    raw = fetch_raw_requirements(appid)
    return parse_requirements(raw)


if __name__ == "__main__":
    import json
    import sys

    query = " ".join(sys.argv[1:]) or "Cyberpunk 2077"
    print(f"Searching Steam for: {query}\n")

    results = search_game(query)
    if not results:
        print("No matches found.")
        sys.exit(0)

    print("Matches:")
    for r in results:
        print(f"  {r['appid']}: {r['name']}")

    top = results[0]
    print(f"\nUsing top match: {top['name']} ({top['appid']})\n")

    requirements = get_game_requirements(top["appid"])
    print(json.dumps(requirements, indent=2))