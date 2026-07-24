"""
Week 4 TODO: wire everything into a FastAPI app.

Endpoints to build out:
  GET  /detect-hardware          -> hardware.detect_hardware()
  GET  /search-game?name=...     -> Steam game search/autocomplete
  GET  /compare?appid=...        -> steam + scoring, detected hardware
  POST /compare-custom           -> steam + scoring, user-entered specs (PC builder mode)
"""

from fastapi import FastAPI
from app.hardware import detect_hardware

app = FastAPI(title="Game Compatibility Checker")


@app.get("/detect-hardware")
def detect_hardware_endpoint():
    """Already functional - Week 1 module wired in early so you can
    hit this from the browser/curl and see it work end to end."""
    return detect_hardware()


# TODO Week 3/4:
# @app.get("/search-game")
# @app.get("/compare")
# @app.post("/compare-custom")
