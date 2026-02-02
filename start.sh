#!/bin/bash

# LudwigOne Startup Script

set -e

echo "🚀 Starting LudwigOne..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set required values (POSTGRES_PASSWORD, SECRET_KEY, MISTRAL_API_KEY)"
    exit 1
fi

# Check required environment variables
source .env

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "❌ Error: POSTGRES_PASSWORD not set in .env"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ Error: SECRET_KEY not set in .env"
    exit 1
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    echo "❌ Error: MISTRAL_API_KEY not set in .env"
    exit 1
fi

echo "✅ Environment variables validated"

# Start services
echo "🐳 Starting Docker services..."

if [ "$1" == "ollama" ]; then
    echo "📦 Starting with Ollama profile..."
    docker-compose --profile ollama up -d
else
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

# Check Postgres
if docker-compose exec -T postgres pg_isready -U ludwigone > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is ready"
else
    echo "⚠️  API is not ready yet (may still be starting)"
fi

# Check Temporal
if curl -s http://localhost:7233 > /dev/null 2>&1; then
    echo "✅ Temporal is ready"
else
    echo "⚠️  Temporal is not ready yet"
fi

echo ""
echo "✅ LudwigOne started successfully!"
echo ""
echo "📍 Service URLs:"
echo "   - API:          http://localhost:8000"
echo "   - API Docs:     http://localhost:8000/docs"
echo "   - Temporal UI:  http://localhost:8080"
echo "   - Frontend:     http://localhost:3000"
echo "   - Dashboard:    http://localhost:3001"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f api"
echo "   docker-compose logs -f worker"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
