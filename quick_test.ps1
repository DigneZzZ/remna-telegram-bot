# Quick bot testing and diagnosis script for Windows
param(
    [string]$Action = "test"
)

Write-Host "🤖 Remnawave Bot Quick Test & Diagnosis" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

function Test-Environment {
    Write-Host "`n🔍 Checking environment..." -ForegroundColor Yellow
    
    if (Test-Path ".env") {
        Write-Host "✅ .env file found" -ForegroundColor Green
        
        $envContent = Get-Content ".env"
        $botToken = $envContent | Where-Object { $_ -like "TELEGRAM_BOT_TOKEN=*" }
        $adminIds = $envContent | Where-Object { $_ -like "ADMIN_USER_IDS=*" }
        
        if ($botToken) {
            $tokenLength = ($botToken -split "=")[1].Length
            Write-Host "✅ TELEGRAM_BOT_TOKEN found (length: $tokenLength)" -ForegroundColor Green
        } else {
            Write-Host "❌ TELEGRAM_BOT_TOKEN not found" -ForegroundColor Red
        }
        
        if ($adminIds) {
            $ids = ($adminIds -split "=")[1]
            Write-Host "✅ ADMIN_USER_IDS found: $ids" -ForegroundColor Green
        } else {
            Write-Host "❌ ADMIN_USER_IDS not found" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ .env file not found" -ForegroundColor Red
    }
}

function Test-BotQuick {
    Write-Host "`n🚀 Starting quick bot test..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the test bot" -ForegroundColor Gray
    
    try {
        python quick_test.py
    } catch {
        Write-Host "❌ Error running quick test: $_" -ForegroundColor Red
    }
}

function Rebuild-Container {
    Write-Host "`n🔨 Rebuilding container..." -ForegroundColor Yellow
    
    Write-Host "Stopping current container..." -ForegroundColor Gray
    docker compose down
    
    Write-Host "Building new image..." -ForegroundColor Gray
    docker compose build --no-cache
    
    Write-Host "Starting container..." -ForegroundColor Gray
    docker compose up -d
    
    Start-Sleep 3
    Write-Host "`n📋 Container logs:" -ForegroundColor Yellow
    docker compose logs --tail=20
}

function Show-Logs {
    Write-Host "`n📋 Current container logs:" -ForegroundColor Yellow
    docker compose logs --tail=50
}

function Diagnose-Issues {
    Write-Host "`n🔍 Running full diagnosis..." -ForegroundColor Yellow
    
    Test-Environment
    
    Write-Host "`n🐳 Docker status:" -ForegroundColor Yellow
    docker compose ps
    
    Show-Logs
    
    Write-Host "`n💡 Troubleshooting tips:" -ForegroundColor Cyan
    Write-Host "1. Make sure your Telegram ID is in ADMIN_USER_IDS" -ForegroundColor White
    Write-Host "2. Verify bot token is correct and bot is not blocked" -ForegroundColor White
    Write-Host "3. Try sending /start to @sendnoteuserbot" -ForegroundColor White
    Write-Host "4. Check if bot username matches token" -ForegroundColor White
}

# Main logic
switch ($Action.ToLower()) {
    "test" {
        Test-Environment
        Test-BotQuick
    }
    "rebuild" {
        Rebuild-Container
    }
    "logs" {
        Show-Logs
    }
    "diagnose" {
        Diagnose-Issues
    }
    default {
        Write-Host "`nUsage: .\quick_test.ps1 [test|rebuild|logs|diagnose]" -ForegroundColor Yellow
        Write-Host "  test     - Quick environment check and bot test" -ForegroundColor White
        Write-Host "  rebuild  - Rebuild and restart container" -ForegroundColor White
        Write-Host "  logs     - Show current container logs" -ForegroundColor White
        Write-Host "  diagnose - Full diagnosis" -ForegroundColor White
    }
}
