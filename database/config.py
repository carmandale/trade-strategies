"""Database configuration and connection management."""
import os
import json
import sqlalchemy as sa
from sqlalchemy import MetaData, event, text as sa_text
try:  # preserve patched symbol if tests set it before module reload
    create_engine  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    from sqlalchemy import create_engine as create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
try:
    from psycopg2.extras import Json as PsycoJson  # type: ignore
except Exception:  # pragma: no cover - optional
    PsycoJson = None  # type: ignore

# Load environment variables
load_dotenv()


def _use_sqlite_env() -> bool:
    """Whether to force SQLite via environment variable."""
    return os.getenv("USE_SQLITE", "false").lower() == "true"

# Allow tests to predefine a mock `get_database_url` before this module executes
if 'get_database_url' not in globals():
    def get_database_url() -> str:
        """Compose a PostgreSQL URL from individual environment variables.
        
        This function intentionally does not implement test fallbacks, as unit
        tests expect this to always return a PostgreSQL URL when env vars are set.
        """
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "trade_strategies")
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Database configuration with sensible defaults
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Allow tests to override the URL via patched get_database_url()
    if _use_sqlite_env():
        DATABASE_URL = "sqlite:///:memory:"
    else:
        DATABASE_URL = get_database_url()

# SQLAlchemy engine configuration. For SQLite, we need special connect args.
is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

if is_sqlite:
    # Enable foreign key constraints in SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[override]
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


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
    if is_sqlite:
        # Strip Postgres-only server defaults (e.g., gen_random_uuid()) before creating tables on SQLite
        for table in Base.metadata.tables.values():
            for column in table.columns:
                sd = getattr(column, "server_default", None)
                if sd is not None:
                    try:
                        text_val = str(getattr(sd, "arg", ""))
                    except Exception:
                        text_val = ""
                    if "gen_random_uuid" in text_val:
                        column.server_default = None
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables in the database (for testing)."""
    Base.metadata.drop_all(bind=engine)


# Auto-create tables when using SQLite to support isolated test runs
if is_sqlite:
    try:
        # Import models so that metadata is populated, then create tables
        import database.models  # noqa: F401
    except Exception:
        # Defer table creation if models import fails; tests may import models later
        pass
    else:
        create_tables()
else:
    # For Postgres or other engines, allow opt-in auto table creation during tests
    if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
        try:
            import database.models  # noqa: F401
        except Exception:
            pass
        else:
            # Ensure extensions needed for UUID defaults exist
            with engine.begin() as conn:
                conn.execute(sa_text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
            create_tables()

    # Adapt dict/list parameters passed via raw text() statements to JSON strings
    # Register globally on Engine class to avoid binding during tests when engine may be mocked
    @event.listens_for(sa.engine.Engine, "before_cursor_execute")
    def _adapt_json_params(conn, cursor, statement, parameters, context, executemany):  # type: ignore[override]
        def _convert(value):
            if isinstance(value, (dict, list)):
                # Use psycopg2 Json wrapper when available to bind as JSONB
                if PsycoJson is not None:
                    return PsycoJson(value)
                return json.dumps(value)
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
            # For Postgres/psycopg, parameters must be a sequence or mapping; ensure mapping values are converted
            converted = {k: _convert(v) for k, v in parameters.items()}
            return statement, converted
        return statement, parameters