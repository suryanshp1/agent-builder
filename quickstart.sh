#!/bin/bash

# AgentBuilder Quick Start Script

set -e

echo "🚀 AgentBuilder Quick Start"
echo "============================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENROUTER_API_KEY"
    echo "   - SERPER_API_KEY"
    echo "   - JWT_SECRET_KEY"
    echo ""
    read -p "Press Enter after you've configured .env..."
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting Docker containers..."
cd infra
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U agentbuilder > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "⚠️  PostgreSQL is not ready yet, please wait..."
fi

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is starting, please wait a moment..."
fi

echo ""
echo "✨ AgentBuilder is running!"
echo ""
echo "📍 Services:"
echo "   Frontend:  http://localhost:80"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"
echo ""
