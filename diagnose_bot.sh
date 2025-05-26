#!/bin/bash

echo "🔍 Диагностика бота..."

echo ""
echo "1. Проверка переменных окружения:"
if [ -f .env ]; then
    echo "✅ Файл .env найден"
    if grep -q "TELEGRAM_BOT_TOKEN" .env; then
        echo "✅ TELEGRAM_BOT_TOKEN найден в .env"
        TOKEN_LENGTH=$(grep "TELEGRAM_BOT_TOKEN" .env | cut -d'=' -f2 | wc -c)
        echo "📏 Длина токена: $TOKEN_LENGTH символов"
    else
        echo "❌ TELEGRAM_BOT_TOKEN НЕ найден в .env"
    fi
    
    if grep -q "ADMIN_USER_IDS" .env; then
        echo "✅ ADMIN_USER_IDS найден в .env"
        ADMIN_IDS=$(grep "ADMIN_USER_IDS" .env | cut -d'=' -f2)
        echo "👥 Admin IDs: $ADMIN_IDS"
    else
        echo "❌ ADMIN_USER_IDS НЕ найден в .env"
    fi
else
    echo "❌ Файл .env НЕ найден"
fi

echo ""
echo "2. Проверка сетевого подключения к Telegram API:"
if curl -s https://api.telegram.org > /dev/null; then
    echo "✅ Подключение к Telegram API работает"
else
    echo "❌ Проблема с подключением к Telegram API"
fi

echo ""
echo "3. Тестирование простого бота:"
echo "🚀 Запуск тестового бота для проверки..."
docker-compose -f docker-compose-test.yml up --build -d

echo ""
echo "4. Проверка логов тестового бота:"
sleep 5
docker-compose -f docker-compose-test.yml logs

echo ""
echo "5. Остановка тестового бота:"
docker-compose -f docker-compose-test.yml down

echo ""
echo "🔍 Диагностика завершена!"
echo ""
echo "📝 Рекомендации:"
echo "1. Попробуйте отправить /start боту @sendnoteuserbot"
echo "2. Убедитесь, что ваш Telegram ID (844586757 или 127192647) правильный"
echo "3. Проверьте логи основного бота: docker compose logs -f"
