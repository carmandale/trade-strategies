# Developer Quick Start

Last Updated: 2025-08-09

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

## Canonical Sources

- Tech stack and commands: `.agent-os/product/tech-stack.md`
- Roadmap and decisions: `.agent-os/product/roadmap.md`, `.agent-os/product/decisions.md`


