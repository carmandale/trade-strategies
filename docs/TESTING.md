# Testing Documentation

## Overview

This project uses PostgreSQL for both production and testing to ensure test reliability and consistency.

## Why PostgreSQL for Tests?

Previously, tests used SQLite which caused several issues:
- **False positives**: SQLite has different SQL syntax and features than PostgreSQL
- **Missing features**: PostgreSQL-specific features (arrays, JSON operators, etc.) couldn't be tested
- **Different behavior**: Transactions, constraints, and indexes behave differently

## Test Infrastructure

### Local Development

Tests require PostgreSQL. You have two options:

#### Option 1: Docker (Recommended)
```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run tests
./run-tests.sh

# Or manually:
pytest tests/
npm run test:run
```

#### Option 2: Local PostgreSQL
```bash
# Create test database
createdb -U postgres test_trade_strategies

# Set environment variable
export DATABASE_URL="postgresql://postgres:password@localhost:5432/test_trade_strategies"

# Run tests
pytest tests/
npm run test:run
```

### CI Environment

GitHub Actions automatically:
1. Spins up PostgreSQL service container
2. Creates test database
3. Runs all tests against real PostgreSQL

## Test Configuration

The test configuration (`tests/conftest.py`) automatically detects the environment:
- **CI**: Uses GitHub Actions PostgreSQL service
- **Local with Docker**: Starts docker-compose test database
- **Local with PostgreSQL**: Uses existing PostgreSQL instance

## Running Tests

### Quick Test Run
```bash
# Run all tests with PostgreSQL
./run-tests.sh
```

### Backend Tests Only
```bash
# Ensure database is running
docker-compose -f docker-compose.test.yml up -d

# Run pytest
source .venv/bin/activate
pytest tests/ -v
```

### Frontend Tests Only
```bash
npm run test:run
```

### E2E Tests
```bash
npm run test:e2e
```

## Troubleshooting

### Docker not running
If you see "Cannot connect to the Docker daemon", either:
1. Start Docker Desktop
2. Or use local PostgreSQL (see Option 2 above)

### Database connection errors
Check that:
1. PostgreSQL is running
2. Test database exists
3. Environment variables are set correctly

### Test failures after migration
When migrating from SQLite to PostgreSQL, some tests may fail due to:
- Different SQL syntax
- Missing database setup
- Mock configurations expecting SQLite

These are being addressed as part of the migration.