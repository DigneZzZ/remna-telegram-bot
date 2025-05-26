# PowerShell deployment script for Remnawave Admin Bot
# Usage: .\deploy.ps1 [-Tag "latest"] [-Environment "production"]

param(
    [string]$Tag = "latest",
    [string]$Environment = "production"
)

# Configuration
$Registry = "ghcr.io"
$ImageName = "dignezzz/remna-telegram-bot"
$ComposeFile = "docker-compose-prod.yml"

Write-Host "🚀 Deploying Remnawave Admin Bot" -ForegroundColor Green
Write-Host "📦 Image: $Registry/$ImageName`:$Tag" -ForegroundColor Cyan
Write-Host "🔧 Environment: $Environment" -ForegroundColor Cyan
Write-Host "📄 Compose file: $ComposeFile" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if compose file exists
if (-not (Test-Path $ComposeFile)) {
    Write-Host "❌ Compose file '$ComposeFile' not found." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Make sure to create it from .env.production template." -ForegroundColor Yellow
    Write-Host "   You can copy: Copy-Item .env.production .env" -ForegroundColor Yellow
    $continue = Read-Host "   Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Pull the latest image
Write-Host "📥 Pulling Docker image..." -ForegroundColor Yellow
docker pull "$Registry/$ImageName`:$Tag"

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker compose -f $ComposeFile down --remove-orphans

# Start new containers
Write-Host "🚀 Starting new containers..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d

# Wait a bit for containers to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check container status
Write-Host "📊 Container status:" -ForegroundColor Cyan
docker compose -f $ComposeFile ps

# Show logs
Write-Host ""
Write-Host "📋 Recent logs (last 20 lines):" -ForegroundColor Cyan
docker compose -f $ComposeFile logs --tail=20

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "🔍 To view logs: docker compose -f $ComposeFile logs -f" -ForegroundColor Cyan
Write-Host "🛑 To stop: docker compose -f $ComposeFile down" -ForegroundColor Cyan
