#!/bin/bash

echo "🤖 Remnawave Bot Quick Fix & Test"
echo "=================================="

# Function to check environment
check_env() {
    echo "🔍 Checking environment..."
    
    if [ -f .env ]; then
        echo "✅ .env file found"
        
        if grep -q "TELEGRAM_BOT_TOKEN" .env; then
            TOKEN_LENGTH=$(grep "TELEGRAM_BOT_TOKEN" .env | cut -d'=' -f2 | wc -c)
            echo "✅ TELEGRAM_BOT_TOKEN found (length: $TOKEN_LENGTH)"
        else
            echo "❌ TELEGRAM_BOT_TOKEN not found"
        fi
        
        if grep -q "ADMIN_USER_IDS" .env; then
            ADMIN_IDS=$(grep "ADMIN_USER_IDS" .env | cut -d'=' -f2)
            echo "✅ ADMIN_USER_IDS found: $ADMIN_IDS"
        else
            echo "❌ ADMIN_USER_IDS not found"
        fi
    else
        echo "❌ .env file not found"
    fi
}

# Function to rebuild and test
rebuild_and_test() {
    echo "🔨 Rebuilding container with fixes..."
    
    echo "Stopping containers..."
    docker compose down
    
    echo "Building new image..."
    docker compose build --no-cache
    
    echo "Starting container..."
    docker compose up -d
    
    echo "Waiting 5 seconds for startup..."
    sleep 5
    
    echo "📋 Container logs:"
    docker compose logs --tail=30
}

# Function to quick test
quick_test() {
    echo "🚀 Starting quick test bot..."
    echo "Send /start to test - Press Ctrl+C to stop"
    python3 quick_test.py
}

# Main menu
case "${1:-help}" in
    "env")
        check_env
        ;;
    "rebuild")
        check_env
        rebuild_and_test
        ;;
    "test")
        quick_test
        ;;
    "logs")
        echo "📋 Current container logs:"
        docker compose logs --tail=50
        ;;
    "fix")
        echo "🔧 Running complete fix..."
        check_env
        rebuild_and_test
        echo ""
        echo "💡 Now try:"
        echo "1. Send /start to @sendnoteuserbot"
        echo "2. Check logs: ./quick_fix.sh logs"
        echo "3. Run test: ./quick_fix.sh test"
        ;;
    *)
        echo "Usage: ./quick_fix.sh [env|rebuild|test|logs|fix]"
        echo "  env     - Check environment variables"
        echo "  rebuild - Rebuild container with fixes"
        echo "  test    - Run quick test bot"
        echo "  logs    - Show container logs"
        echo "  fix     - Complete fix and rebuild"
        ;;
esac
