#!/usr/bin/env python
"""Script to fix test issues without requiring a real database."""

import os
import sys
from pathlib import Path

# Set test environment variables
test_env = {
    'DATABASE_URL': 'sqlite:///:memory:',  # Use in-memory SQLite for tests
    'DB_NAME': 'test_trade_strategies',
    'DATABASE_ECHO': 'false',
    'AUTO_CREATE_TABLES': 'true',
    'OPENAI_API_KEY': 'sk-test-key-12345',  # Proper format test key
    'OPENAI_MODEL': 'gpt-4',
    'TESTING': 'true'
}

# Apply environment variables
for key, value in test_env.items():
    os.environ[key] = value

# Now patch the database configuration before it's imported
import database.config

# Replace PostgreSQL with SQLite for testing
original_create_engine = database.config.create_engine

def mock_create_engine(url, **kwargs):
    """Replace PostgreSQL URL with SQLite for testing."""
    if 'postgresql' in url:
        url = 'sqlite:///:memory:'
    # Remove PostgreSQL-specific options
    kwargs.pop('pool_pre_ping', None)
    return original_create_engine(url, **kwargs)

# Apply the patch
database.config.create_engine = mock_create_engine
database.config.DATABASE_URL = 'sqlite:///:memory:'

# Recreate the engine with SQLite
database.config.engine = mock_create_engine(
    database.config.DATABASE_URL,
    echo=False
)

# Update SessionLocal to use new engine
from sqlalchemy.orm import sessionmaker
database.config.SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=database.config.engine
)

print("Test environment configured:")
print(f"  - Database: SQLite in-memory")
print(f"  - OpenAI Key: {os.environ['OPENAI_API_KEY'][:10]}...")
print(f"  - Testing Mode: Enabled")
print()

# Run pytest with the modified configuration
import subprocess
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
    capture_output=False
)

sys.exit(result.returncode)