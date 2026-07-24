"""
Week 3 TODO: Steam data pipeline.

Plan:
- GET https://store.steampowered.com/api/appdetails?appids={appid}
  returns JSON with a `pc_requirements` field containing raw HTML
  for minimum/recommended specs.
- Parse that HTML (BeautifulSoup) to pull out CPU/GPU/RAM/storage
  lines. Formatting is NOT standardized across games, so this needs
  fallback regex patterns and will need iterating on real examples.
- Cache parsed results locally (SQLite) keyed by appid, since
  hitting Steam's API repeatedly for the same game is wasteful.
"""

import requests

STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


def fetch_raw_requirements(appid: int) -> dict:
    resp = requests.get(STEAM_APPDETAILS_URL, params={"appids": appid}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get(str(appid), {}).get("data", {}).get("pc_requirements", {})


def parse_requirements(raw_html: dict) -> dict:
    raise NotImplementedError("Week 3: parse min/recommended HTML into structured fields")
