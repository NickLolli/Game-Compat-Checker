# Frontend (React + Vite)

## Setup

```bash
npm install
npm run dev
```

Then open http://localhost:5173. Requires the backend running at
http://127.0.0.1:8000 (see backend/README) - start that first.

## Structure

```
src/
├── App.jsx                    # top-level state + layout
├── api.js                     # fetch wrappers for backend endpoints
├── index.css                  # design tokens (colors, fonts, spacing)
└── components/
    ├── SearchBar.jsx          # game search input
    ├── GameResultsList.jsx    # pick among multiple Steam matches
    └── VerdictCard.jsx        # the verdict/bottleneck readout panel
```

## Still TODO

- Custom PC builder form (calls `/compare-custom` - backend endpoint
  already exists, just needs a form UI)
- Loading/error states could use more polish
- Currently a single page - no routing needed yet
