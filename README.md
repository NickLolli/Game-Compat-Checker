# Can It Run? — Game Compatibility Checker

Detects your PC's real hardware and tells you whether it can run any Steam
game — plus which component to upgrade if it can't. Also supports a custom
PC builder mode where you type in hypothetical parts instead (backend ready,
frontend form still TODO).

## Project structure

```
game-compat-checker/
├── backend/                  # Python (FastAPI) API
│   └── app/
│       ├── main.py             # FastAPI endpoints
│       ├── hardware.py         # Local hardware detection (WMI on Windows)
│       ├── steam.py            # Live Steam search + requirement parsing
│       ├── scoring.py          # Comparison/verdict logic
│       ├── benchmarks.py       # CPU/GPU benchmark score table + fuzzy matching
│       └── check_game.py       # CLI test harness (search -> compare -> verdict)
├── frontend/                 # React (Vite) UI
│   └── src/
│       ├── App.jsx              # Top-level state + layout
│       ├── api.js               # Fetch wrappers for the backend
│       └── components/
│           ├── SearchBar.jsx
│           ├── GameResultsList.jsx
│           └── VerdictCard.jsx  # The verdict/bottleneck readout panel
└── README.md
```

## Roadmap

- [x] Week 1 — Hardware detection (`hardware.py`)
- [x] Week 2 — Scoring/verdict system (`scoring.py`, `benchmarks.py`)
- [x] Week 3 — Live Steam data pipeline (`steam.py`)
- [x] Week 4 — FastAPI backend (`main.py`)
- [x] Week 5-6 — React frontend
- [x] Week 7+ — Custom PC builder form, polish, deploy

## Getting started

You need **two terminals** running at once - the backend API and the
frontend dev server.

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

Clear Cache: Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

Runs at http://127.0.0.1:8000 — visit `/docs` for interactive API testing.

### 2. Frontend

In a **separate terminal** (no venv needed - that's Python-only):

```bash
cd frontend
npm install
npm run dev
```

Runs at http://localhost:5173 — open this in your browser. It talks to the
backend automatically.

## Notes

- GPU/CPU detection currently only implemented for Windows (via WMI, so it
  works for NVIDIA/AMD/Intel alike). Other platforms return placeholder values.
- Benchmark scores in `benchmarks.py` are rough relative-performance numbers,
  not precise FPS predictions — good enough for a "Good / Playable /
  Unplayable" verdict, not scientific benchmarking. The table needs to grow
  over time as new hardware releases.
- Steam's requirements text isn't standardized across games, so `steam.py`'s
  parser is forgiving but occasionally can't extract a field cleanly -
  `scoring.py` reports those as "unmatched" rather than guessing.
- The backend reads whatever hardware it's running on (`/compare`), so it's
  meant to run locally on your own machine, not as a shared public server.

## License

MIT