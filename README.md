# Game Compatibility Checker

Detects your PC's hardware (or lets you enter custom parts), looks up a game's
requirements on Steam, and tells you whether it'll run — plus which component
to upgrade if it won't.

## Project structure

```
game-compat-checker/
├── backend/          # Python (FastAPI) API
│   └── app/
│       ├── main.py           # API entrypoint
│       ├── hardware.py       # Local hardware detection (psutil/GPUtil)
│       ├── steam.py          # Steam appdetails fetch + requirement parsing
│       ├── scoring.py        # Benchmark lookup + comparison/verdict logic
│       └── benchmarks.py     # CPU/GPU benchmark score table
├── frontend/         # React app
└── README.md
```

## Roadmap

- [x] Week 1 — Hardware detection (`hardware.py`)
- [ ] Week 2 — Scoring/verdict system (`scoring.py`, `benchmarks.py`)
- [ ] Week 3 — Steam data pipeline (`steam.py`)
- [ ] Week 4 — FastAPI backend wiring (`main.py`)
- [ ] Week 5-6 — React frontend
- [ ] Week 7+ — Polish, deploy

## Getting started (backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/hardware.py        # sanity check: prints your detected specs
```

## License

MIT
