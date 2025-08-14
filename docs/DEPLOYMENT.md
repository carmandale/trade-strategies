# Deployment Guide

Last Updated: 2025-08-14

This app is deployed as:

- Backend: FastAPI on Render (Python Web Service)
- Frontend: Vite/React on Vercel (static site)

The backend must expose `/health` and bind to `$PORT`. The frontend calls the backend via `VITE_API_URL`.

## Prerequisites

- Render account (Web Service + Postgres)
- Vercel account
- Node 18+ and npm (for local builds / CLI)

Optional CLIs:
- `render` CLI (login required for logs): `brew install render` then `render login`
- `vercel` CLI: `npm i -g vercel` then `vercel login`

## Environment Variables

Backend (Render):
- `DATABASE_URL`: Render Postgres Internal Connection String
- `OPENAI_API_KEY`: your OpenAI key
- `FRONTEND_URL`: your Vercel site URL (for CORS)
- `AUTO_CREATE_TABLES`: `true` for the first deploy (the API will create tables); can be disabled later

Frontend (Vercel):
- `VITE_API_URL`: `https://YOUR_RENDER_SERVICE.onrender.com`
- `VITE_BASE_PATH`: `/`

## Backend on Render (Python Web Service)

Recommended (no Docker):
- Environment: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Database:
- Add a Render Postgres. In the Web Service → Environment, set `DATABASE_URL` to the Postgres Internal Connection String.
- For first deployment, set `AUTO_CREATE_TABLES=true` to auto-create schema. Alternatively, run Alembic migrations manually.

Verify after deploy:
```bash
curl -s https://YOUR_RENDER_SERVICE.onrender.com/health
curl -s https://YOUR_RENDER_SERVICE.onrender.com/
```
Expected shape:
```json
{"status":"healthy","service":"trade-strategies-api","version":"1.0.0","port":"<port>"}
```

Common issues:
- 502 or test app content: ensure it’s a Python Web Service and the Start Command matches the line above. If using Docker, ensure the Dockerfile runs `uvicorn api.main:app` and binds `$PORT`.
- DB connection refused/localhost: ensure `DATABASE_URL` is set to the Render Postgres Internal Connection String, not localhost.
- CORS errors: set `FRONTEND_URL` to the Vercel URL.

### Using Docker on Render (optional)
If you must use Docker, the included `Dockerfile` starts uvicorn against `api.main:app` and binds `$PORT`. Render will build and run it automatically.

## Frontend on Vercel (Vite)

This repo includes `vercel.json` with:
- `installCommand`: `npm install --legacy-peer-deps`
- `buildCommand`: `vite build`
- `outputDirectory`: `dist`
- `rewrites`: all routes → `/` (SPA)

Option A: Connect Git repo
1) New Project → Import repo.
2) Set env vars in Project Settings → Environment Variables:
   - `VITE_API_URL = https://YOUR_RENDER_SERVICE.onrender.com`
   - `VITE_BASE_PATH = /`
3) Deploy. Future pushes auto‑deploy.

Option B: Deploy via CLI (no Git connection required)
```bash
vercel --yes --prod \
  -e VITE_API_URL=https://YOUR_RENDER_SERVICE.onrender.com \
  -e VITE_BASE_PATH=/
```

Make deployments deterministic and fast:
- Add a `.vercelignore` to exclude Python backend and infra so Vercel ships only the Vite app.
- Example `.vercelignore` contents:
```
api/
database/
alembic/
services/
weekly/
monthly/
daily/
scripts/
start.sh
Dockerfile
render.yaml
railway.toml
nixpacks.toml
requirements.txt
railway_requirements.txt
playwright*/
vitest.config.ts
pytest.ini
docs/
*.md
node_modules/
```

Verify after deploy:
```bash
curl -sI https://YOUR_VERCEL_APP.vercel.app | head -20
```
Open the site → DevTools → Network: API calls should hit `https://YOUR_RENDER_SERVICE.onrender.com` and return 200s.

## Alembic Migrations (optional)

If you prefer migrations over `AUTO_CREATE_TABLES`, use Alembic:
1) Add a Render Shell command or Job to run:
```bash
alembic upgrade head
```
Ensure `DATABASE_URL` is set in the environment when running this.

## End‑to‑End Validation Checklist

- Backend `/health` returns the Trade Strategies API JSON (not the test app message)
- Backend root `/` returns `{ "message": "Trade Strategies API", "version": "1.0.0" }`
- DB‑using endpoints work (e.g., `/api/ai/market-data`) without connection errors
- Frontend loads on Vercel and calls the Render backend successfully

## Troubleshooting

- 502 on Render: Start command must be `uvicorn api.main:app --host 0.0.0.0 --port $PORT`. If using Docker, ensure the CMD does the same and `$PORT` is passed.
- Seeing `{ "app": "simple_test_app" }`: that’s a legacy test app. You’re running the wrong entrypoint. Use the Start Command above or the provided Dockerfile.
- `connection to server at "localhost" refused`: wrong DB URL; use Render’s Internal Connection String in `DATABASE_URL`.
- CORS blocked: set `FRONTEND_URL` on the backend to your Vercel URL.

## File References

- Backend app: `api/main.py` (health, CORS, routers)
- DB config: `database/config.py` (`DATABASE_URL`, `AUTO_CREATE_TABLES`)
- Render blueprint (optional): `render.yaml`
- Vercel config: `vercel.json`
- Dev startup: `start.sh`


