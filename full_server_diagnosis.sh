#!/bin/bash
# Скрипт для полной диагностики и исправления бота на сервере

echo "🚀 Полная диагностика и исправление Remnawave Admin Bot"
echo "============================================================"

cd ~/remna-telegram-bot

echo -e "\n1. 📋 Текущий статус контейнеров:"
docker-compose -f docker-compose-prod.yml ps

echo -e "\n2. 🔧 Проверка переменных окружения в контейнере:"
docker exec remnawave-admin-bot-dev env | grep -E "(API_BASE_URL|ADMIN_USER_IDS|TELEGRAM_BOT_TOKEN|REMNAWAVE_API_TOKEN)"

echo -e "\n3. 🛑 Остановка контейнеров..."
docker-compose -f docker-compose-prod.yml down

echo -e "\n4. 🔨 Пересборка с очисткой кэша..."
docker-compose -f docker-compose-prod.yml build --no-cache

echo -e "\n5. 🚀 Запуск контейнеров..."
docker-compose -f docker-compose-prod.yml up -d

echo -e "\n6. ⏳ Ожидание запуска (15 секунд)..."
sleep 15

echo -e "\n7. 📊 Статус после запуска:"
docker-compose -f docker-compose-prod.yml ps

echo -e "\n8. 📋 Последние логи (поиск проблем авторизации):"
docker-compose -f docker-compose-prod.yml logs --tail=50 | grep -E "(Authorization check|ADMIN_USER_IDS|Parsed|Unauthorized|Error|started|conversation|DEBUG)"

echo -e "\n9. 🔍 Проверка процесса загрузки конфигурации:"
docker-compose -f docker-compose-prod.yml logs --tail=100 | grep -E "(Raw ADMIN_USER_IDS|Parsed ADMIN_USER_IDS|Environment check|Admin user IDs)"

echo -e "\n10. 🐛 Все логи за последние 30 строк:"
docker-compose -f docker-compose-prod.yml logs --tail=30

echo -e "\n✅ Диагностика завершена!"
echo -e "\n📝 Что проверить далее:"
echo "1. Отправьте /start боту @sendnoteuserbot"
echo "2. Проверьте появились ли новые логи: docker-compose -f docker-compose-prod.yml logs -f"
echo "3. Если проблема остается, проверьте логи в реальном времени при отправке /start"

echo -e "\n🔄 Для мониторинга в реальном времени используйте:"
echo "docker-compose -f docker-compose-prod.yml logs -f --tail=10"
