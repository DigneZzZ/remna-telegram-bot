# Debug script for Remnawave Admin Bot
Write-Host "🔍 Checking Docker container status..." -ForegroundColor Cyan

try {
    $containers = docker ps --format "table {{.Names}}" | Select-String "remnawave"
    if ($containers) {
        Write-Host "✅ Found remnawave containers:" -ForegroundColor Green
        $containers | ForEach-Object { Write-Host "   $_" }
        
        $containerName = ($containers | Select-Object -First 1).ToString().Trim()
        Write-Host "`n📦 Using container: $containerName" -ForegroundColor Yellow
        
        Write-Host "`n🔧 Running environment check..." -ForegroundColor Cyan
        docker exec $containerName python check_env.py
        
        Write-Host "`n📋 Recent logs:" -ForegroundColor Cyan
        docker logs --tail 20 $containerName
    } else {
        Write-Host "❌ No remnawave containers running" -ForegroundColor Red
        Write-Host "Please start the bot first:" -ForegroundColor Yellow
        Write-Host "   docker-compose -f docker-compose-prod.yml up -d" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Error accessing Docker: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure Docker is installed and running" -ForegroundColor Yellow
}
