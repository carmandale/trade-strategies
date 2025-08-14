# Trade Strategies

FastAPI backend + Vite/React frontend for options strategy analysis and backtesting (e.g., Iron Condors) with real‑time routes and charts.

## Quick Start

Prereqs: Python (uv recommended), Node 18+, Postgres.

1) Create a local Postgres DB and set env in `.env` (see `docs/DEV.md`).
2) Start everything:

```bash
./start.sh
```

Backend: `http://127.0.0.1:8000` (health: `/health`)

Frontend: `http://localhost:3000`

More details: `docs/DEV.md`.

## Deployment

Recommended: Backend on Render, Frontend on Vercel.

- Backend (Render, Python Web Service):
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  - Env: `DATABASE_URL`, `OPENAI_API_KEY`, `FRONTEND_URL`, `AUTO_CREATE_TABLES=true` (first deploy)
- Frontend (Vercel):
  - Env: `VITE_API_URL=https://<your-render>.onrender.com`, `VITE_BASE_PATH=/`
  - Uses `vercel.json` for build and SPA rewrites

Full step‑by‑step guide: `docs/DEPLOYMENT.md`.

## Health Checks

- Backend: `GET /health` → JSON `{ status, service, version, port }`
- Root: `GET /` → `{ message: "Trade Strategies API", version: "1.0.0" }`

## Repo Structure

- `api/` FastAPI app (entry: `api/main.py`)
- `database/` SQLAlchemy config and models
- `src/` Vite/React frontend
- `docs/` Developer and deployment docs
- `start.sh` Local dev runner

