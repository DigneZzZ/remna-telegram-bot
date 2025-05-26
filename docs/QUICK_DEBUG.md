# Быстрая диагностика бота

## Шаг 1: Узнайте свой Telegram ID

Если у вас нет .env файла или вы не знаете свой Telegram ID:

```bash
# Создайте .env файл с токеном бота
echo "TELEGRAM_BOT_TOKEN=ваш_токен_бота" > .env

# Запустите ID бота
docker compose -f docker-compose-debug.yml --profile id-bot up --build

# Напишите боту любое сообщение - он покажет ваш ID
# Остановите ID бота: Ctrl+C
```

## Шаг 2: Настройте .env файл

Создайте файл `.env` с правильными значениями:

```bash
API_BASE_URL=https://ваш-сервер.com/api
REMNAWAVE_API_TOKEN=ваш_токен_апи
TELEGRAM_BOT_TOKEN=ваш_токен_бота
ADMIN_USER_IDS=123456789
```

**Важно:** `ADMIN_USER_IDS` должен содержать ваш реальный Telegram ID!

## Шаг 3: Запустите бота в debug режиме

```bash
# Запустите с подробным логированием
docker compose -f docker-compose-debug.yml --profile debug up --build

# В другом терминале смотрите логи
docker logs -f remnawave-admin-bot-debug
```

## Шаг 4: Протестируйте бота

1. Напишите боту команду `/start`
2. Проверьте логи - должно появиться сообщение об авторизации
3. Если бот не отвечает, проверьте ADMIN_USER_IDS в логах

## Частые проблемы:

❌ **Бот не отвечает** - проверьте ADMIN_USER_IDS  
❌ **"Unauthorized access"** - ваш ID не в ADMIN_USER_IDS  
❌ **"API token not set"** - проверьте REMNAWAVE_API_TOKEN  
❌ **"Bot token not set"** - проверьте TELEGRAM_BOT_TOKEN  

## Полезные команды:

```bash
# Посмотреть переменные окружения в контейнере
docker exec remnawave-admin-bot-debug env | grep -E "(ADMIN|TELEGRAM|REMNAWAVE)"

# Остановить все контейнеры
docker compose -f docker-compose-debug.yml down

# Пересобрать с нуля
docker compose -f docker-compose-debug.yml build --no-cache
```
