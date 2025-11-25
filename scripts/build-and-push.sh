#!/bin/bash

# Script to build and push HomeGuard image to Docker Hub
# Usage: ./scripts/build-and-push.sh [DOCKERHUB_USERNAME] [TAG]

set -e

# Get Docker Hub username from argument or prompt
DOCKERHUB_USERNAME=${1:-"YOUR_DOCKERHUB_USERNAME"}
TAG=${2:-"latest"}

if [ "$DOCKERHUB_USERNAME" == "YOUR_DOCKERHUB_USERNAME" ]; then
    echo "Error: Please provide your Docker Hub username"
    echo "Usage: ./scripts/build-and-push.sh <dockerhub_username> [tag]"
    exit 1
fi

IMAGE_NAME="$DOCKERHUB_USERNAME/homeguard:$TAG"

echo "=========================================="
echo "Building and Pushing HomeGuard to Docker Hub"
echo "=========================================="
echo "Docker Hub Username: $DOCKERHUB_USERNAME"
echo "Image: $IMAGE_NAME"
echo "=========================================="
echo ""

# Check if user is logged in to Docker Hub (check for auth in config)
if [ ! -f ~/.docker/config.json ] || ! grep -q "auths" ~/.docker/config.json 2>/dev/null; then
    echo "Warning: Docker Hub authentication not found."
    echo "If push fails, please login first: docker login"
    echo ""
fi

# Build the image using docker compose (it will tag it correctly)
echo "Step 1: Building image..."
docker compose build homeguard

# Push to Docker Hub
echo ""
echo "Step 2: Pushing to Docker Hub..."
docker push $IMAGE_NAME

echo ""
echo "=========================================="
echo "✅ Successfully pushed $IMAGE_NAME to Docker Hub"
echo "=========================================="
echo ""
echo "To use on Orange Pi, update docker-compose.prod.yml with:"
echo "  image: $IMAGE_NAME"
echo ""
echo "Then run on Orange Pi:"
echo "  docker compose -f docker-compose.prod.yml pull"
echo "  docker compose -f docker-compose.prod.yml up -d"

