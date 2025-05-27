#!/bin/bash

echo "=== Docker Network Diagnostics ==="
echo

echo "1. Checking Docker networks..."
docker network ls

echo
echo "2. Checking running containers..."
docker ps -a

echo
echo "3. Checking remnawave-network details..."
docker network inspect remnawave-network 2>/dev/null || echo "Network remnawave-network not found"

echo
echo "4. Testing connectivity from bot container..."
if docker ps --format "table {{.Names}}" | grep -q "remna-telegram-bot-prod"; then
    echo "Bot container is running, testing connectivity..."
    docker exec remna-telegram-bot-prod ping -c 3 remnawave 2>/dev/null || echo "Cannot ping remnawave from bot container"
    docker exec remna-telegram-bot-prod nslookup remnawave 2>/dev/null || echo "Cannot resolve remnawave hostname"
    docker exec remna-telegram-bot-prod curl -s -o /dev/null -w "%{http_code}" http://remnawave:3000/api 2>/dev/null || echo "Cannot connect to remnawave API"
else
    echo "Bot container is not running"
fi

echo
echo "5. Testing API endpoint from host..."
if docker ps --format "table {{.Names}}" | grep -q "remnawave"; then
    echo "Remnawave container is running, testing from host..."
    curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000/api 2>/dev/null || echo "Cannot connect to localhost:3000"
else
    echo "Remnawave container is not running"
fi

echo
echo "=== Network Setup Commands ==="
echo "To create the network manually:"
echo "docker network create remnawave-network"
echo
echo "To start with full compose:"
echo "docker-compose -f docker-compose-full.yml up -d"
echo
echo "To start only the bot (if Remnawave is running separately):"
echo "docker-compose -f docker-compose-prod.yml up -d"
