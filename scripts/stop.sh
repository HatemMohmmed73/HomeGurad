#!/bin/bash

# HomeGuard Stop Script

echo "🛑 Stopping HomeGuard..."

# Navigate to project directory
cd "$(dirname "$0")/.."

# Stop all containers
docker-compose down

echo "✅ HomeGuard stopped successfully!"

