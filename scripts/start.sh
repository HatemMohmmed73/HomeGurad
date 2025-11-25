#!/bin/bash

# HomeGuard Startup Script

echo "🚀 Starting HomeGuard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your configuration before continuing."
    exit 1
fi

# Build and start containers
echo "🏗️  Building containers..."
docker-compose build

echo "🎬 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec backend python init_db.py

# Show status
echo ""
echo "✅ HomeGuard is running!"
echo ""
echo "📊 Access Dashboard: http://localhost:3000"
echo "🔌 API Endpoint: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🔑 Default Credentials:"
echo "   Email: admin@homeguard.local"
echo "   Password: admin123"
echo ""
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"

