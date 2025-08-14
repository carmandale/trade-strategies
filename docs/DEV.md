# Developer Quick Start

Last Updated: 2025-08-14

This project is uv-only (Python) and PostgreSQL-only (database).

## Prerequisites

- uv installed (macOS: `brew install uv`)
- Node.js 18+ and npm
- PostgreSQL 14+ running locally

## Environment

Backend (`.env`):

```
DB_USER=your_user
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=trade_strategies
# Optional
API_PORT=8000
AUTO_CREATE_TABLES=true
```

Frontend (`.env.local`, optional):

```
PORT=3000
```

## First Run

1) Create the database (once):

```
createdb -h 127.0.0.1 -p 5432 -U "$USER" trade_strategies
```

2) Start everything:

```
./start.sh
```

The script will:
- Create/activate `.venv` via uv
- Install Python deps via `uv pip install -r requirements.txt`
- Start FastAPI with uvicorn
- Start Vite dev server (React)

Ports are chosen dynamically starting from `API_PORT` (backend) and `PORT` (frontend).

## Local dev parity & safety

- Use the same env names as production; create `.env` (backend) and `.env.local` (frontend).
- For DB, run a local Postgres container with the same database name:
```
docker run --name ts-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=trade_strategies -p 5432:5432 -d postgres:16
```
- Apply migrations locally:
```
alembic -c alembic.ini upgrade head
```
- Smoke tests mirroring prod endpoints:
```
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/ai/market-data
```

## Production push checklist

1) Backend (Render)
- Commit and push to `main`.
- Ensure Render service runtime is Python, not Docker.
- Env set: `DATABASE_URL`, `OPENAI_API_KEY`, `FRONTEND_URL`, `AUTO_CREATE_TABLES=false`.
- One-off job (if needed):
```
render jobs create <SERVICE_ID> --start-command "alembic -c alembic.ini upgrade head" --confirm -o text
```
- Health check:
```
curl -s https://<service>.onrender.com/health
```

2) Frontend (Vercel)
- Deploy with env:
```
vercel --yes --prod -e VITE_API_URL=https://<service>.onrender.com -e VITE_BASE_PATH=/
```
- Verify:
  - Site loads.
  - Network calls to `/api/*` return 200.

## Testing

Backend (Postgres only):

```
DB_USER="$USER" DB_PASSWORD="" DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=trade_strategies_test AUTO_CREATE_TABLES=true \
.venv/bin/pytest -q
```

Frontend:

```
npm run test:run
```

## Troubleshooting

- Free ports if needed:

```
for p in 8000 8001 3000 3001; do lsof -t -iTCP:$p -sTCP:LISTEN | xargs -r kill -9; done
pkill -f "uvicorn .*api.main:app" || true
pkill -f vite || true
```

- Ensure the extension for UUID defaults is present; this is handled automatically when `AUTO_CREATE_TABLES=true`.

## Legacy Notes Cleanup

- The old root FastAPI app (`main.py`) and its `/analyze` endpoint have been removed. Use the API under `api/main.py` and routes in `api/routes/*`.
- Frontend should call:
  - `GET /current_price/{symbol}` and `GET /historical_data/{symbol}` for market data
  - `POST /api/strategies/backtest` for backtests
  - `GET/POST/DELETE /api/trades` for trade management

## Canonical Sources

- Tech stack and commands: `.agent-os/product/tech-stack.md`
- Roadmap and decisions: `.agent-os/product/roadmap.md`, `.agent-os/product/decisions.md`

## Deployment

See `docs/DEPLOYMENT.md` for step-by-step instructions (Render backend, Vercel frontend), required env vars, and verification.


