# ✅ ИСПРАВЛЕНИЯ DOCKER COMPOSE КОМАНД

## Что было исправлено

Во всех файлах проекта команды `docker-compose` заменены на современный `docker compose` (без тире), в соответствии с новой версией Docker Compose v2.

### Исправленные файлы:

#### 🔧 Скрипты развертывания:
- `deploy.ps1` - PowerShell скрипт развертывания
- `deploy.sh` - Bash скрипт развертывания  
- `diagnose.ps1` - PowerShell диагностика
- `diagnose.sh` - Bash диагностика

#### 📚 Документация:
- `README.md` - Основная документация
- `QUICKSTART.md` - Быстрый старт
- `QUICK_DEBUG.md` - Быстрая диагностика
- `TROUBLESHOOTING.md` - Решение проблем
- `DEPLOYMENT.md` - Развертывание
- `DEPLOYMENT_CHECKLIST.md` - Чек-лист развертывания

### Примеры исправленных команд:

#### Раньше:
```bash
docker-compose up -d
docker-compose -f docker-compose-prod.yml up --build -d
docker-compose logs -f
docker-compose down
```

#### Теперь:
```bash
docker compose up -d
docker compose -f docker-compose-prod.yml up --build -d
docker compose logs -f
docker compose down
```

## Почему это важно?

1. **Современный стандарт** - Docker Compose v2 использует команду без тире
2. **Совместимость** - Новые версии Docker могут не поддерживать старую команду
3. **Консистентность** - Все команды теперь единообразны в проекте

## Обратная совместимость

Если у пользователя старая версия Docker, он может:
1. Обновить Docker до последней версии (рекомендуется)
2. Создать алиас: `alias docker-compose='docker compose'`
3. Использовать команды как есть - большинство систем поддерживают обе версии

## Проверка

Для проверки какая версия команды доступна:
```bash
# Проверить Docker Compose v2
docker compose version

# Проверить старую версию
docker-compose --version
```

Все исправления применены корректно и готовы к использованию! 🎉
