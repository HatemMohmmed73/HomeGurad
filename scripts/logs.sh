#!/bin/bash

# HomeGuard Logs Script

echo "📋 Viewing HomeGuard logs..."
echo "Press Ctrl+C to exit"
echo ""

# Navigate to project directory
cd "$(dirname "$0")/.."

# Show logs
docker-compose logs -f --tail=100

