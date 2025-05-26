#!/bin/bash

# Deployment script for Remnawave Admin Bot
# Usage: ./deploy.sh [tag] [environment]

set -e

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="dignezzz/remna-telegram-bot"
DEFAULT_TAG="latest"
DEFAULT_ENV="production"

# Get parameters
TAG=${1:-$DEFAULT_TAG}
ENVIRONMENT=${2:-$DEFAULT_ENV}
COMPOSE_FILE="docker-compose-prod.yml"

echo "🚀 Deploying Remnawave Admin Bot"
echo "📦 Image: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
echo "🔧 Environment: ${ENVIRONMENT}"
echo "📄 Compose file: ${COMPOSE_FILE}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "❌ Compose file '$COMPOSE_FILE' not found."
    exit 1
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "⚠️  .env file not found. Make sure to create it from .env.production template."
    echo "   You can copy: cp .env.production .env"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Pull the latest image
echo "📥 Pulling Docker image..."
docker pull ${REGISTRY}/${IMAGE_NAME}:${TAG}

# Update the image tag in compose file if not 'latest'
if [[ "$TAG" != "latest" ]]; then
    echo "🔄 Updating image tag to ${TAG}..."
    sed -i.bak "s|image: ${REGISTRY}/${IMAGE_NAME}:.*|image: ${REGISTRY}/${IMAGE_NAME}:${TAG}|" $COMPOSE_FILE
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Start new containers
echo "🚀 Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Restore original compose file if we modified it
if [[ "$TAG" != "latest" && -f "${COMPOSE_FILE}.bak" ]]; then
    mv ${COMPOSE_FILE}.bak $COMPOSE_FILE
fi

# Wait a bit for containers to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose -f $COMPOSE_FILE ps

# Show logs
echo ""
echo "📋 Recent logs (last 20 lines):"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo ""
echo "✅ Deployment completed successfully!"
echo "🔍 To view logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "🛑 To stop: docker-compose -f $COMPOSE_FILE down"
