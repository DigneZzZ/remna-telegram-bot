#!/bin/bash
# Automated Diagnostic Script for Remnawave Admin Bot
# This script will automatically diagnose and attempt to fix common issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

print_color() {
    echo -e "${2}${1}${NC}"
}

print_step() {
    echo
    print_color "🔹 Шаг $1: $2" "$CYAN"
}

check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_color "✅ Docker установлен: $DOCKER_VERSION" "$GREEN"
        return 0
    else
        print_color "❌ Docker не найден. Установите Docker." "$RED"
        print_color "   Инструкции: https://docs.docker.com/get-docker/" "$YELLOW"
        return 1
    fi
}

check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        print_color "✅ docker-compose найден" "$GREEN"
        return 0
    elif docker compose version &> /dev/null; then
        print_color "✅ docker compose найден" "$GREEN"
        alias docker-compose='docker compose'
        return 0
    else
        print_color "❌ docker-compose не найден" "$RED"
        return 1
    fi
}

check_env_file() {
    if [ -f ".env" ]; then
        print_color "✅ Файл .env найден" "$GREEN"
        
        REQUIRED_VARS=("TELEGRAM_BOT_TOKEN" "REMNAWAVE_API_TOKEN" "ADMIN_USER_IDS" "API_BASE_URL")
        
        for var in "${REQUIRED_VARS[@]}"; do
            if grep -q "^${var}=" .env; then
                VALUE=$(grep "^${var}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" | xargs)
                if [ -n "$VALUE" ] && [ "$VALUE" != "your_token_here" ]; then
                    print_color "✅ $var настроен" "$GREEN"
                else
                    print_color "❌ $var не настроен или пустой" "$RED"
                fi
            else
                print_color "❌ $var отсутствует в .env" "$RED"
            fi
        done
        return 0
    else
        print_color "❌ Файл .env не найден" "$RED"
        return 1
    fi
}

get_telegram_id() {
    print_step "1" "Запуск ID бота для получения Telegram ID"
    
    if [ ! -f ".env" ]; then
        echo -n "Введите TELEGRAM_BOT_TOKEN: "
        read -r BOT_TOKEN
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" > .env
    fi
    
    print_color "🤖 Запускаю ID бота..." "$YELLOW"
    print_color "📱 Напишите боту любое сообщение для получения вашего Telegram ID" "$CYAN"
    print_color "⏹️  Нажмите Ctrl+C для остановки после получения ID" "$YELLOW"
    
    docker compose -f docker-compose-debug.yml --profile id-bot up --build
}

start_debug_mode() {
    print_step "2" "Запуск бота в режиме отладки"
    
    if ! check_env_file; then
        print_color "❌ Настройте файл .env перед запуском debug режима" "$RED"
        return 1
    fi
    
    print_color "🐛 Запускаю бота в debug режиме..." "$YELLOW"
    print_color "📋 Смотрите логи для диагностики проблем" "$CYAN"
    
    # Stop any running containers first
    docker compose -f docker-compose-prod.yml down 2>/dev/null || true
    docker compose -f docker-compose-debug.yml down 2>/dev/null || true
    
    # Start in debug mode
    docker compose -f docker-compose-debug.yml --profile debug up --build
}

check_environment() {
    print_step "3" "Проверка переменных окружения в контейнере"
    
    CONTAINER_NAME="remnawave-admin-bot-debug"
    
    if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_color "✅ Контейнер $CONTAINER_NAME работает" "$GREEN"
        
        echo
        print_color "🔍 Проверяю переменные окружения..." "$CYAN"
        docker exec "$CONTAINER_NAME" python check_env.py
        
        echo
        print_color "📋 Последние логи:" "$CYAN"
        docker logs --tail 20 "$CONTAINER_NAME"
    else
        print_color "❌ Контейнер $CONTAINER_NAME не запущен" "$RED"
        print_color "   Запустите: ./diagnose.sh debug" "$YELLOW"
    fi
}

run_full_diagnostic() {
    print_color "🔍 ПОЛНАЯ ДИАГНОСТИКА REMNAWAVE ADMIN BOT" "$MAGENTA"
    print_color "=================================================" "$MAGENTA"
    
    # Step 1: Check Docker
    print_step "1" "Проверка Docker"
    if ! check_docker || ! check_docker_compose; then
        return 1
    fi
    
    # Step 2: Check .env file
    print_step "2" "Проверка конфигурации"
    ENV_EXISTS=0
    check_env_file && ENV_EXISTS=1
    
    # Step 3: Check running containers
    print_step "3" "Проверка запущенных контейнеров"
    CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep remnawave || true)
    if [ -n "$CONTAINERS" ]; then
        print_color "✅ Найдены контейнеры Remnawave:" "$GREEN"
        echo "$CONTAINERS" | while read -r line; do
            print_color "   $line" "$NC"
        done
    else
        print_color "❌ Контейнеры Remnawave не запущены" "$YELLOW"
    fi
    
    # Step 4: Recommendations
    print_step "4" "Рекомендации"
    
    if [ $ENV_EXISTS -eq 0 ]; then
        print_color "🎯 СЛЕДУЮЩИЕ ШАГИ:" "$YELLOW"
        print_color "1. Получите Telegram ID: ./diagnose.sh telegram-id" "$NC"
        print_color "2. Настройте .env файл с полученным ID" "$NC"
        print_color "3. Запустите debug режим: ./diagnose.sh debug" "$NC"
    elif [ -z "$CONTAINERS" ]; then
        print_color "🎯 СЛЕДУЮЩИЕ ШАГИ:" "$YELLOW"
        print_color "1. Запустите debug режим: ./diagnose.sh debug" "$NC"
        print_color "2. Проверьте логи авторизации" "$NC"
        print_color "3. Напишите боту /start и проверьте ответ" "$NC"
    else
        print_color "🎯 БОТ РАБОТАЕТ! Проверьте:" "$GREEN"
        print_color "1. Напишите боту /start" "$NC"
        print_color "2. Если не отвечает - проверьте ADMIN_USER_IDS" "$NC"
        print_color "3. Проверьте логи: ./diagnose.sh check-env" "$NC"
    fi
}

# Main execution logic
print_color "🤖 Remnawave Admin Bot - Диагностика v2.0" "$MAGENTA"

case "${1:-}" in
    "telegram-id"|"id")
        get_telegram_id
        ;;
    "debug")
        start_debug_mode
        ;;
    "check-env"|"env")
        check_environment
        ;;
    "full"|"diagnostic"|"")
        run_full_diagnostic
        ;;
    *)
        print_color "Использование:" "$CYAN"
        print_color "  ./diagnose.sh [full]         # Полная диагностика (по умолчанию)" "$NC"
        print_color "  ./diagnose.sh telegram-id    # Получить Telegram ID" "$NC"
        print_color "  ./diagnose.sh debug          # Запуск в режиме отладки" "$NC"
        print_color "  ./diagnose.sh check-env      # Проверка переменных окружения" "$NC"
        echo
        print_color "Быстрый старт: ./diagnose.sh" "$YELLOW"
        ;;
esac
