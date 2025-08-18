#!/bin/bash
# Script to run tests with proper environment setup

# Set environment variables for testing
export DATABASE_URL="postgresql://$USER@localhost/trade_strategies_test"
export AUTO_CREATE_TABLES=true
export OPENAI_API_KEY="sk-test-key-12345"
export OPENAI_MODEL="gpt-4"
export CI="true"  # Some tests check for CI environment

# Create test database if it doesn't exist
createdb -U $USER trade_strategies_test 2>/dev/null || true

# Activate virtual environment
source .venv/bin/activate

# Install any missing dependencies
uv pip install pytest pytest-asyncio psycopg2-binary 2>/dev/null

# Run tests with verbose output
python -m pytest tests/ -v --tb=short "$@"