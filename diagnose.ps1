# Automated Diagnostic Script for Remnawave Admin Bot
# This script will automatically diagnose and attempt to fix common issues

param(
    [switch]$GetTelegramId,
    [switch]$DebugMode,
    [switch]$CheckEnv,
    [switch]$FullDiagnostic
)

$ErrorActionPreference = "Continue"

function Write-ColorOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param($StepNumber, $Description)
    Write-ColorOutput "`n🔹 Шаг $StepNumber`: $Description" "Cyan"
}

function Check-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-ColorOutput "✅ Docker установлен: $dockerVersion" "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Docker не найден. Установите Docker Desktop для Windows." "Red"
        Write-ColorOutput "   Скачать: https://www.docker.com/products/docker-desktop" "Yellow"
        return $false
    }
}

function Check-EnvFile {
    if (Test-Path ".env") {
        Write-ColorOutput "✅ Файл .env найден" "Green"
        
        $envContent = Get-Content ".env" -Raw
        $requiredVars = @("TELEGRAM_BOT_TOKEN", "REMNAWAVE_API_TOKEN", "ADMIN_USER_IDS", "API_BASE_URL")
        
        foreach ($var in $requiredVars) {
            if ($envContent -match "$var\s*=\s*(.+)") {
                $value = $matches[1].Trim()
                if ($value -and $value -ne "your_token_here" -and $value -ne "") {
                    Write-ColorOutput "✅ $var настроен" "Green"
                } else {
                    Write-ColorOutput "❌ $var не настроен или пустой" "Red"
                }
            } else {
                Write-ColorOutput "❌ $var отсутствует в .env" "Red"
            }
        }
        return $true
    } else {
        Write-ColorOutput "❌ Файл .env не найден" "Red"
        return $false
    }
}

function Get-TelegramUserId {
    Write-Step "1" "Запуск ID бота для получения Telegram ID"
    
    if (-not (Test-Path ".env")) {
        $botToken = Read-Host "Введите TELEGRAM_BOT_TOKEN"
        "TELEGRAM_BOT_TOKEN=$botToken" | Out-File -FilePath ".env" -Encoding UTF8
    }
    
    Write-ColorOutput "🤖 Запускаю ID бота..." "Yellow"
    Write-ColorOutput "📱 Напишите боту любое сообщение для получения вашего Telegram ID" "Cyan"
    Write-ColorOutput "⏹️  Нажмите Ctrl+C для остановки после получения ID" "Yellow"
      try {
        docker compose -f docker-compose-debug.yml --profile id-bot up --build
    } catch {
        Write-ColorOutput "❌ Ошибка запуска ID бота: $($_.Exception.Message)" "Red"
    }
}

function Start-DebugMode {
    Write-Step "2" "Запуск бота в режиме отладки"
    
    if (-not (Check-EnvFile)) {
        Write-ColorOutput "❌ Настройте файл .env перед запуском debug режима" "Red"
        return
    }
    
    Write-ColorOutput "🐛 Запускаю бота в debug режиме..." "Yellow"
    Write-ColorOutput "📋 Смотрите логи для диагностики проблем" "Cyan"
      try {
        # Stop any running containers first
        docker compose -f docker-compose-prod.yml down 2>$null
        docker compose -f docker-compose-debug.yml down 2>$null
        
        # Start in debug mode
        docker compose -f docker-compose-debug.yml --profile debug up --build
    } catch {
        Write-ColorOutput "❌ Ошибка запуска debug режима: $($_.Exception.Message)" "Red"
    }
}

function Check-Environment {
    Write-Step "3" "Проверка переменных окружения в контейнере"
    
    $containerName = "remnawave-admin-bot-debug"
    
    # Check if container is running
    $containerStatus = docker ps --format "table {{.Names}}" | Select-String $containerName
    
    if ($containerStatus) {
        Write-ColorOutput "✅ Контейнер $containerName работает" "Green"
        
        Write-ColorOutput "`n🔍 Проверяю переменные окружения..." "Cyan"
        docker exec $containerName python check_env.py
        
        Write-ColorOutput "`n📋 Последние логи:" "Cyan"
        docker logs --tail 20 $containerName
    } else {
        Write-ColorOutput "❌ Контейнер $containerName не запущен" "Red"
        Write-ColorOutput "   Запустите: .\diagnose.ps1 -DebugMode" "Yellow"
    }
}

function Run-FullDiagnostic {
    Write-ColorOutput "🔍 ПОЛНАЯ ДИАГНОСТИКА REMNAWAVE ADMIN BOT" "Magenta"
    Write-ColorOutput "=" * 50 "Magenta"
    
    # Step 1: Check Docker
    Write-Step "1" "Проверка Docker"
    if (-not (Check-DockerInstalled)) {
        return
    }
    
    # Step 2: Check .env file
    Write-Step "2" "Проверка конфигурации"
    $envExists = Check-EnvFile
    
    # Step 3: Check running containers
    Write-Step "3" "Проверка запущенных контейнеров"
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "remnawave"
    if ($containers) {
        Write-ColorOutput "✅ Найдены контейнеры Remnawave:" "Green"
        $containers | ForEach-Object { Write-ColorOutput "   $_" "White" }
    } else {
        Write-ColorOutput "❌ Контейнеры Remnawave не запущены" "Yellow"
    }
    
    # Step 4: Recommendations
    Write-Step "4" "Рекомендации"
    
    if (-not $envExists) {
        Write-ColorOutput "🎯 СЛЕДУЮЩИЕ ШАГИ:" "Yellow"
        Write-ColorOutput "1. Получите Telegram ID: .\diagnose.ps1 -GetTelegramId" "White"
        Write-ColorOutput "2. Настройте .env файл с полученным ID" "White"
        Write-ColorOutput "3. Запустите debug режим: .\diagnose.ps1 -DebugMode" "White"
    } elseif (-not $containers) {
        Write-ColorOutput "🎯 СЛЕДУЮЩИЕ ШАГИ:" "Yellow"
        Write-ColorOutput "1. Запустите debug режим: .\diagnose.ps1 -DebugMode" "White"
        Write-ColorOutput "2. Проверьте логи авторизации" "White"
        Write-ColorOutput "3. Напишите боту /start и проверьте ответ" "White"
    } else {
        Write-ColorOutput "🎯 БОТ РАБОТАЕТ! Проверьте:" "Green"
        Write-ColorOutput "1. Напишите боту /start" "White"
        Write-ColorOutput "2. Если не отвечает - проверьте ADMIN_USER_IDS" "White"
        Write-ColorOutput "3. Проверьте логи: .\diagnose.ps1 -CheckEnv" "White"
    }
}

# Main execution logic
Write-ColorOutput "🤖 Remnawave Admin Bot - Диагностика v2.0" "Magenta"

if ($GetTelegramId) {
    Get-TelegramUserId
} elseif ($DebugMode) {
    Start-DebugMode
} elseif ($CheckEnv) {
    Check-Environment
} elseif ($FullDiagnostic) {
    Run-FullDiagnostic
} else {
    Write-ColorOutput "Использование:" "Cyan"
    Write-ColorOutput "  .\diagnose.ps1 -FullDiagnostic    # Полная диагностика (рекомендуется)" "White"
    Write-ColorOutput "  .\diagnose.ps1 -GetTelegramId    # Получить Telegram ID" "White"
    Write-ColorOutput "  .\diagnose.ps1 -DebugMode        # Запуск в режиме отладки" "White"
    Write-ColorOutput "  .\diagnose.ps1 -CheckEnv         # Проверка переменных окружения" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Быстрый старт: .\diagnose.ps1 -FullDiagnostic" "Yellow"
}
