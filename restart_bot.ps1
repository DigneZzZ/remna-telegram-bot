#!/usr/bin/env pwsh
# Script to restart the bot with debugging

Write-Host "🔄 Перезапуск Remnawave Admin Bot..." -ForegroundColor Yellow

# Stop current containers
Write-Host "🛑 Остановка контейнеров..." -ForegroundColor Yellow
docker-compose -f docker-compose-prod.yml down

# Rebuild with fresh config
Write-Host "🔨 Пересборка контейнеров..." -ForegroundColor Yellow
docker-compose -f docker-compose-prod.yml build --no-cache

# Start with logging
Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Yellow
docker-compose -f docker-compose-prod.yml up -d

# Wait a bit
Start-Sleep -Seconds 5

# Show logs
Write-Host "📋 Логи контейнера:" -ForegroundColor Green
docker-compose -f docker-compose-prod.yml logs --tail=50

Write-Host "`n✅ Готово! Проверьте бота отправив /start" -ForegroundColor Green
