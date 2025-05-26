# Диагностика проблем с Remnawave Admin Bot

## Проблема: Бот не отвечает на сообщения

### Возможные причины:
1. **Неправильно настроены ADMIN_USER_IDS** - наиболее вероятная причина
2. Проблемы с авторизацией
3. Проблемы с конфигурацией ConversationHandler
4. Проблемы с API подключением

### Шаги диагностики:

#### 1. Проверить статус контейнера
```bash
# Проверить запущен ли контейнер
docker ps | grep remnawave

# Посмотреть логи контейнера
docker logs remnawave-admin-bot-remnawave-bot-1 --tail 50

# Посмотреть логи в реальном времени
docker logs -f remnawave-admin-bot-remnawave-bot-1
```

#### 2. Проверить переменные окружения
```bash
# Зайти в контейнер
docker exec -it remnawave-admin-bot-remnawave-bot-1 bash

# Внутри контейнера проверить переменные
echo $ADMIN_USER_IDS
echo $TELEGRAM_BOT_TOKEN
echo $REMNAWAVE_API_TOKEN

# Запустить скрипт проверки
python check_env.py
```

#### 3. Получить свой Telegram ID
Чтобы получить свой Telegram ID:
1. Напишите боту @userinfobot
2. Он покажет ваш User ID
3. Добавьте этот ID в ADMIN_USER_IDS в .env файле

#### 4. Проверить .env файл
Убедитесь что в директории проекта есть файл `.env` с правильными значениями:
```bash
REMNAWAVE_API_TOKEN=ваш_токен_апи
TELEGRAM_BOT_TOKEN=ваш_токен_бота
ADMIN_USER_IDS=123456789,987654321
API_BASE_URL=https://ваш-сервер.com/api
```

#### 5. Перезапустить бота с новыми настройками
```bash
# Остановить контейнер
docker compose -f docker-compose-prod.yml down

# Пересобрать и запустить с новыми переменными
docker compose -f docker-compose-prod.yml up --build -d

# Посмотреть логи запуска
docker compose -f docker-compose-prod.yml logs -f remnawave-bot
```

### Частые ошибки:

1. **ADMIN_USER_IDS не настроен** - бот будет отклонять всех пользователей
2. **Неправильный формат ADMIN_USER_IDS** - должен быть: `123456789,987654321`
3. **Пробелы в ADMIN_USER_IDS** - не должно быть пробелов: `123,456` ✅, `123, 456` ❌
4. **Нет файла .env** - переменные не загрузятся

### Полезные команды:

```bash
# Посмотреть все переменные окружения в контейнере
docker exec remnawave-admin-bot-remnawave-bot-1 env | grep -E "(ADMIN|TELEGRAM|REMNAWAVE)"

# Перезапустить только бота (без пересборки)
docker compose -f docker-compose-prod.yml restart remnawave-bot

# Посмотреть ресурсы контейнера
docker stats remnawave-admin-bot-remnawave-bot-1

# Проверить сетевые подключения
docker exec remnawave-admin-bot-remnawave-bot-1 ping telegram.org
```
