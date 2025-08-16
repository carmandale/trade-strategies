#!/bin/bash

# Script to run tests with PostgreSQL locally

echo "🧪 Running tests with PostgreSQL..."

# Start PostgreSQL test database if not running
echo "📦 Ensuring PostgreSQL test database is running..."
docker-compose -f docker-compose.test.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_retries=10
for i in $(seq 1 $max_retries); do
    if docker-compose -f docker-compose.test.yml exec -T test-db pg_isready -U testuser -d test_trade_strategies > /dev/null 2>&1; then
        echo "✅ Database ready!"
        break
    fi
    if [ $i -eq $max_retries ]; then
        echo "❌ Database failed to start"
        exit 1
    fi
    sleep 1
done

# Run backend tests
echo ""
echo "🐍 Running backend tests..."
source .venv/bin/activate
pytest tests/ -v

# Run frontend tests
echo ""
echo "🎨 Running frontend tests..."
npm run test:run

echo ""
echo "✅ All tests completed!"

# Optional: Stop test database
read -p "Stop test database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose.test.yml down
    echo "🛑 Test database stopped"
fi