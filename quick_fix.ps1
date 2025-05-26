# Quick fix script for Remnawave Bot issues
param(
    [string]$Action = "help"
)

Write-Host "🤖 Remnawave Bot Quick Fix & Test" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

function Check-Environment {
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

function Rebuild-Container {
    Write-Host "`n🔨 Rebuilding container with fixes..." -ForegroundColor Yellow
    
    Write-Host "Stopping containers..." -ForegroundColor Gray
    docker compose down
    
    Write-Host "Building new image..." -ForegroundColor Gray
    docker compose build --no-cache
    
    Write-Host "Starting container..." -ForegroundColor Gray
    docker compose up -d
    
    Write-Host "Waiting 5 seconds for startup..." -ForegroundColor Gray
    Start-Sleep 5
    
    Write-Host "`n📋 Container logs:" -ForegroundColor Yellow
    docker compose logs --tail=30
}

function Test-BotQuick {
    Write-Host "`n🚀 Starting quick test bot..." -ForegroundColor Yellow
    Write-Host "Send /start to test - Press Ctrl+C to stop" -ForegroundColor Gray
    
    try {
        python quick_test.py
    } catch {
        Write-Host "❌ Error running test: $_" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "`n📋 Current container logs:" -ForegroundColor Yellow
    docker compose logs --tail=50
}

function Complete-Fix {
    Write-Host "`n🔧 Running complete fix..." -ForegroundColor Yellow
    
    Check-Environment
    Rebuild-Container
    
    Write-Host "`n💡 Now try:" -ForegroundColor Cyan
    Write-Host "1. Send /start to @sendnoteuserbot" -ForegroundColor White
    Write-Host "2. Check logs: .\quick_fix.ps1 logs" -ForegroundColor White
    Write-Host "3. Run test: .\quick_fix.ps1 test" -ForegroundColor White
}

# Main logic
switch ($Action.ToLower()) {
    "env" {
        Check-Environment
    }
    "rebuild" {
        Check-Environment
        Rebuild-Container
    }
    "test" {
        Test-BotQuick
    }
    "logs" {
        Show-Logs
    }
    "fix" {
        Complete-Fix
    }
    default {
        Write-Host "`nUsage: .\quick_fix.ps1 [env|rebuild|test|logs|fix]" -ForegroundColor Yellow
        Write-Host "  env     - Check environment variables" -ForegroundColor White
        Write-Host "  rebuild - Rebuild container with fixes" -ForegroundColor White
        Write-Host "  test    - Run quick test bot" -ForegroundColor White
        Write-Host "  logs    - Show container logs" -ForegroundColor White
        Write-Host "  fix     - Complete fix and rebuild" -ForegroundColor White
    }
}
