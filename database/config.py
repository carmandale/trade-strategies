"""Database configuration and connection management (PostgreSQL-only)."""
import os
import json
import sqlalchemy as sa
from urllib.parse import urlparse
from sqlalchemy import MetaData, event, text as sa_text
# Preserve patched symbol if tests patch before reload
try:
    create_engine  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    create_engine = sa.create_engine  # type: ignore
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
# Optional JSON binder from psycopg2 if available
try:  # pragma: no cover - optional dependency in CI
    from psycopg2.extras import Json as PsycoJson  # type: ignore
except Exception:  # pragma: no cover
    PsycoJson = None  # type: ignore

def _load_render_secrets() -> None:
    """Best-effort load of secrets from Render's /etc/secrets mount.

    Supports two patterns:
    - .env-style file (e.g., /etc/secrets/.env) parsed via python-dotenv
    - Key-named files (e.g., /etc/secrets/DATABASE_URL) whose contents are the value
    """
    secrets_dir = "/etc/secrets"
    try:  # pragma: no cover
        if not os.path.isdir(secrets_dir):
            return

        # First, load any .env file present
        env_path = os.path.join(secrets_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)

        # Then, for key-named files, read and export
        for name in os.listdir(secrets_dir):
            full = os.path.join(secrets_dir, name)
            if os.path.isdir(full):
                continue
            # Skip the .env we already loaded
            if name == ".env":
                continue
            # Only accept reasonable key names
            if all(c.isupper() or c.isdigit() or c == '_' for c in name):
                try:
                    with open(full, "r", encoding="utf-8") as fh:
                        value = fh.read().strip()
                    if value:
                        os.environ.setdefault(name, value)
                except Exception:
                    continue
    except Exception:
        # Non-fatal; env can still be provided by standard mechanisms
        pass

# Load environment variables from standard .env and Render Secret Files
load_dotenv()
_load_render_secrets()


# Allow tests to predefine a mock `get_database_url` before this module executes
try:
    get_database_url  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    def get_database_url() -> str:
        """Compose a PostgreSQL URL from individual environment variables."""
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "trade_strategies")
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Database configuration (Postgres only)
# Prefer managed connection strings if present (Render exposes DATABASE_URL or DATABASE_INTERNAL_URL)
_managed_db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_INTERNAL_URL")
DATABASE_URL = _managed_db_url if _managed_db_url else get_database_url()

# Emit minimal diagnostics about the DB target without leaking credentials
try:  # pragma: no cover
    parsed = urlparse(DATABASE_URL)
    db_host = parsed.hostname or "<none>"
    db_name = (parsed.path or "/").lstrip("/") or "<none>"
    print(f"[database.config] Using DATABASE_URL host={db_host} db={db_name}")
except Exception:
    pass
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def _ensure_uuid_defaults_and_extensions() -> None:
    """Ensure required DB extensions and UUID defaults exist at the DB level.

    Some tests perform raw SQL INSERTs without specifying the `id` value and
    expect the database itself to generate UUIDs via `gen_random_uuid()`.
    This function makes sure the `pgcrypto` extension is available and that
    `id` columns on core tables have a server-side default of `gen_random_uuid()`.
    """
    try:
        from sqlalchemy import text as _text

        with engine.begin() as conn:
            # Ensure pgcrypto is available for gen_random_uuid()
            conn.execute(_text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

            # Helper DO block to set default only if not already present
            def _set_default_for(table: str, column: str = "id") -> None:
                conn.execute(_text(f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_attrdef d
        JOIN pg_class c ON c.oid = d.adrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
        WHERE n.nspname = 'public' AND c.relname = '{table}' AND a.attname = '{column}'
    ) THEN
        ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT gen_random_uuid();
    END IF;
END$$;
"""))

            # Apply to all core tables that use UUID primary keys
            for tbl in ("strategies", "backtests", "trades", "market_data_cache"):
                _set_default_for(tbl)
    except Exception:
        # Non-fatal: if we cannot modify DB defaults (e.g., permissions), leave as-is.
        # Tests that rely on these defaults will surface issues if this fails.
        pass


# Ensure DB-side UUID defaults are present as early as possible
_ensure_uuid_defaults_and_extensions()


def get_db():
    """Get database session with automatic cleanup.
    This matches the FastAPI dependency injection pattern.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Keep the old name for backward compatibility
get_db_session = get_db


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables in the database (for testing)."""
    Base.metadata.drop_all(bind=engine)


# Auto-create tables in test contexts if requested
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    try:
        import database.models  # noqa: F401
    except Exception:
        pass
    else:
        with engine.begin() as conn:
            conn.execute(sa_text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        create_tables()


# Adapt dict/list parameters passed via raw text() statements to JSON strings
@event.listens_for(sa.engine.Engine, "before_cursor_execute")
def _adapt_json_params(conn, cursor, statement, parameters, context, executemany):  # type: ignore[override]
    def _convert(value):
        if isinstance(value, (dict, list)):
            return PsycoJson(value) if PsycoJson is not None else json.dumps(value)
        return value

    if isinstance(parameters, (list, tuple)):
        new_params = []
        for param_set in parameters:
            if isinstance(param_set, (list, tuple)):
                new_params.append([_convert(v) for v in param_set])
            elif isinstance(param_set, dict):
                new_params.append({k: _convert(v) for k, v in param_set.items()})
            else:
                new_params.append(param_set)
        return statement, new_params
    elif isinstance(parameters, dict):
        converted = {k: _convert(v) for k, v in parameters.items()}
        return statement, converted
    return statement, parameters