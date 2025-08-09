"""Database configuration and connection management (PostgreSQL-only)."""
import os
import json
import sqlalchemy as sa
from sqlalchemy import MetaData, event, text as sa_text
# Preserve patched symbol if tests patch before reload
try:
    create_engine  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    create_engine = sa.create_engine  # type: ignore
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from psycopg2.extras import Json as PsycoJson  # type: ignore

# Load environment variables
load_dotenv()


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
DATABASE_URL = os.getenv("DATABASE_URL", get_database_url())
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
            return PsycoJson(value)
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