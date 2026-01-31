#!/bin/bash
set -e

echo "=== Recipe Ideator Deployment ==="
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and configure your secrets:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Pull latest code (if in a git repo)
if [ -d .git ]; then
    echo "Pulling latest code..."
    git pull origin main || echo "Git pull skipped (not on main or no remote)"
fi

# Build and start services
echo ""
echo "Building containers..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."
sleep 10

# Run data ingestion if requested
if [ "$1" == "--ingest" ]; then
    echo ""
    echo "Running data ingestion..."
    echo "  - Loading data into PostgreSQL..."
    docker compose -f docker-compose.prod.yml exec -T api uv run python -m src.data_ingestion.pg_loader
    echo "  - Loading data into Neo4j..."
    docker compose -f docker-compose.prod.yml exec -T api uv run python -m src.data_ingestion.kg_loader
    echo "Data ingestion complete!"
fi

# Health check
echo ""
echo "Checking API health..."
if curl -sf http://localhost/api/health > /dev/null; then
    echo "API is healthy!"
else
    echo "WARNING: API health check failed. Check logs with:"
    echo "  docker compose -f docker-compose.prod.yml logs api"
fi

echo ""
echo "=== Deployment complete ==="
echo ""
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Access the application at: http://localhost (or your server's public IP)"
