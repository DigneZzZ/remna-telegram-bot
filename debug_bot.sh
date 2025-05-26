#!/bin/bash
echo "🔍 Checking Docker container status..."
docker ps | grep remnawave || echo "❌ No remnawave containers running"

echo ""
echo "🔍 Checking environment variables in container..."
if docker ps | grep remnawave > /dev/null; then
    CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep remnawave | head -1)
    echo "📦 Container: $CONTAINER_NAME"
    
    echo ""
    echo "🔧 Running environment check..."
    docker exec $CONTAINER_NAME python check_env.py
    
    echo ""
    echo "📋 Recent logs:"
    docker logs --tail 20 $CONTAINER_NAME
else
    echo "❌ No remnawave container found. Please start the bot first:"
    echo "   docker-compose -f docker-compose-prod.yml up -d"
fi
