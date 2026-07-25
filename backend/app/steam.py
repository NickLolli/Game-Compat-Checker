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

def search_game(name: str, max_results: int = 5) -> list[dict]:
    """Returns a list of {"appid": int, "name": str} candidates.
    The caller (or the user, if there are multiple matches) should
    pick the right one - e.g. searching "Doom" returns several games.
    """
    resp = requests.get(
        STORE_SEARCH_URL,
        params={"term": name, "cc": "us", "l": "english"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    return [
        {"appid": item["id"], "name": item["name"]}
        for item in data.get("items", [])[:max_results]
    ]


# ---------------------------------------------------------------
# Step 2: fetch raw requirements HTML for a specific App ID
# ---------------------------------------------------------------

def fetch_raw_requirements(appid: int) -> dict:
    """Returns Steam's raw pc_requirements block:
    {"minimum": "<html>...", "recommended": "<html>..."}
    Some games only have "minimum" and no "recommended", or vice versa.
    """
    resp = requests.get(
        APPDETAILS_URL, params={"appids": appid, "cc": "us", "l": "english"}, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()

    app_data = data.get(str(appid), {})
    if not app_data.get("success"):
        raise ValueError(f"Steam returned no data for appid {appid}")

    return app_data.get("data", {}).get("pc_requirements", {})


# ---------------------------------------------------------------
# Step 3: parse the messy HTML into clean {cpu, gpu, ram_gb}
# ---------------------------------------------------------------

# Steam's requirement lines use varying labels for the same thing -
# try each of these, in order, for a given field.
_CPU_LABELS = ["processor", "cpu"]
_GPU_LABELS = ["graphics", "video card", "gpu"]
_RAM_LABELS = ["memory", "ram"]


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
    or_split = re.split(r"\s+or\s+", text, maxsplit=1, flags=re.IGNORECASE)
    comma_split = text.split(",", 1)

    if len(or_split) > 1 and (len(comma_split) == 1 or len(or_split[0]) <= len(comma_split[0])):
        first = or_split[0]
    else:
        first = comma_split[0]

    return first.strip()


def _parse_tier(html: str) -> dict:
    """Parse one tier (minimum or recommended) into {cpu, gpu, ram_gb}."""
    lines = _extract_list_items(html)
    return {
        "cpu": _first_alternative(_find_field(lines, _CPU_LABELS)),
        "gpu": _first_alternative(_find_field(lines, _GPU_LABELS)),
        "ram_gb": _extract_ram_gb(_find_field(lines, _RAM_LABELS)),
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