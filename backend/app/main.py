"""
Week 4: FastAPI app wiring hardware.py + steam.py + scoring.py into
real HTTP endpoints.

Endpoints:
  GET  /detect-hardware                  -> your machine's detected specs
  GET  /search-game?name=...             -> list of matching Steam games
  GET  /compare?appid=...                -> verdict using YOUR detected hardware
  POST /compare-custom                   -> verdict using USER-ENTERED specs (PC builder mode)

Run with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs
(FastAPI generates this automatically - genuinely useful for testing
each endpoint by hand before the frontend exists).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app.hardware import detect_hardware
from app.steam import search_game, get_game_requirements
from app.scoring import compare_specs

app = FastAPI(title="Game Compatibility Checker")

# Allow the React frontend (running on a different port during dev,
# e.g. localhost:5173 for Vite) to call this API from the browser.
# Tighten this to a specific origin before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/detect-hardware")
def detect_hardware_endpoint():
    return detect_hardware()


@app.get("/search-game")
def search_game_endpoint(name: str = Query(..., min_length=1)):
    results = search_game(name)
    if not results:
        raise HTTPException(status_code=404, detail=f"No Steam games found matching '{name}'")
    return results


@app.get("/compare")
def compare_endpoint(appid: int):
    """Compares the SERVER's detected hardware (i.e. whoever's
    machine is running this backend) against a game's requirements.
    This only makes sense when the backend runs locally on the user's
    own machine - which is the intended setup for this app."""
    try:
        requirements = get_game_requirements(appid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Couldn't reach Steam - check your internet connection and try again")

    user_specs = detect_hardware()
    return compare_specs(user_specs, requirements)


# ---------------------------------------------------------------
# Custom PC builder mode: user types in specs instead of using
# whatever hardware this backend happens to be running on.
# ---------------------------------------------------------------

class CustomSpecs(BaseModel):
    cpu_name: str
    gpu_name: str
    ram_gb: float


@app.post("/compare-custom")
def compare_custom_endpoint(specs: CustomSpecs, appid: int):
    try:
        requirements = get_game_requirements(appid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Couldn't reach Steam - check your internet connection and try again")

    # Reuse the exact same comparison engine as /compare - just feed
    # it hand-typed specs instead of detected ones, in the same shape
    # compare_specs() expects.
    user_specs = {
        "cpu": {"name": specs.cpu_name},
        "ram": {"total_gb": specs.ram_gb},
        "gpus": [{"name": specs.gpu_name}],
    }
    return compare_specs(user_specs, requirements)


# ---------------------------------------------------------------
# Manual game entry: for non-Steam games (Epic, GOG, itch.io, etc.)
# where there's no API to pull requirements from. The user copies
# min/recommended specs from wherever they found them, and we run
# them through the exact same comparison engine - compare_specs()
# doesn't care where the data came from.
# ---------------------------------------------------------------

class ManualTier(BaseModel):
    cpu: str | None = None
    gpu: str | None = None
    ram_gb: float | None = None


class ManualGameRequirements(BaseModel):
    game_name: str
    minimum: ManualTier
    recommended: ManualTier | None = None


@app.post("/compare-manual")
def compare_manual_endpoint(payload: ManualGameRequirements):
    requirements = {
        "minimum": payload.minimum.model_dump(),
        "recommended": (
            payload.recommended.model_dump()
            if payload.recommended
            else {"cpu": None, "gpu": None, "ram_gb": None}
        ),
    }
    user_specs = detect_hardware()
    result = compare_specs(user_specs, requirements)
    result["game_name"] = payload.game_name
    return result