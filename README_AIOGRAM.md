# Remnawave Telegram Bot - Aiogram Edition

## 🎉 Миграция завершена!

Бот успешно мигрирован с `python-telegram-bot` на `aiogram` для решения конфликта зависимостей httpx.

## ⚡ Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка .env файла
Отредактируйте `.env` файл:
```env
# Telegram Bot Configuration  
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Remnawave API Configuration
REMNAWAVE_API_TOKEN=your_api_token_here
API_BASE_URL=http://your-remnawave-server:3000/api

# Admin User IDs (через запятую)
ADMIN_USER_IDS=123456789,987654321

# Logging
LOG_LEVEL=INFO
```

### 3. Запуск бота
```bash
# Новая версия на Aiogram
python main_aiogram.py

# Старая версия (пока доступна)  
python main.py
```

### 4. Docker запуск
```bash
# Новый compose файл для Aiogram
docker-compose -f docker-compose-aiogram.yml up -d

# Старый compose файл
docker-compose up -d
```

## 📋 Доступные команды

- `/start` - Запуск бота и главное меню
- Главное меню включает:
  - 👥 Управление пользователями
  - 🔧 Управление серверами (в разработке)
  - 📊 Статистика (в разработке)
  - 🌐 Управление хостами (в разработке)  
  - 📥 Входящие соединения (в разработке)
  - 📦 Массовые операции (в разработке)

## 🔧 Различия версий

### Aiogram версия (`main_aiogram.py`)
- ✅ Асинхронная архитектура
- ✅ Совместимость с httpx >= 0.27.2
- ✅ FSM (Finite State Machine) для диалогов
- ✅ Современный Router-based подход
- ✅ Улучшенная обработка ошибок

### Legacy версия (`main.py`)  
- ⚠️ Конфликт httpx версий
- ⚠️ Синхронная архитектура
- ⚠️ ConversationHandler подход

## 🐛 Отладка

### Проверка статуса
```bash
python check_status.py
```

### Проверка конфликтов
```bash
python -c "import httpx, aiogram, remnawave_api; print('OK')"
```

### Уровни логирования
Установите в `.env`:
- `LOG_LEVEL=DEBUG` - для разработки
- `LOG_LEVEL=INFO` - для продакшн (рекомендуется)
- `LOG_LEVEL=ERROR` - минимальные логи

## 📁 Структура проекта

```
├── main_aiogram.py              # Новый основной файл (Aiogram)
├── main.py                      # Старый файл (python-telegram-bot)
├── requirements.txt             # Обновленные зависимости
├── .env                         # Конфигурация
├── modules/
│   ├── config.py               # Общая конфигурация
│   ├── handlers_aiogram/       # Новые обработчики
│   │   ├── auth.py            # Авторизация
│   │   ├── start_handler.py   # /start команда
│   │   ├── menu_handler.py    # Главное меню
│   │   ├── user_handlers.py   # Управление пользователями
│   │   └── *.py               # Другие обработчики
│   └── handlers/              # Старые обработчики
└── docker-compose-aiogram.yml  # Docker для Aiogram
```

## 🚀 Производственное развертывание

1. **Настройте .env с реальными токенами**
2. **Установите LOG_LEVEL=INFO** 
3. **Используйте Docker для стабильности**
4. **Настройте мониторинг логов**

## ❓ Поддержка

- Документация миграции: `MIGRATION_SUCCESS.md`
- Проблемы: создайте issue в репозитории
- Тестирование: запустите `migration_test.py`

---
**Версия**: Aiogram 3.20.0  
**Статус**: ✅ Готов к продакшн
