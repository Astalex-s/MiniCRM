# Одна команда: поднять контейнеры (API + фронтенд) и открыть приложение в браузере.
# Из корня проекта: .\docker\run.ps1
# Требуется: Docker Engine
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host "Сборка и запуск контейнеров (crm-api, crm-frontend)..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.yml up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка запуска Docker Compose." -ForegroundColor Red
    exit 1
}

Write-Host "Ожидание готовности приложения (до 45 сек)..." -ForegroundColor Cyan
$maxAttempts = 15
$attempt = 0
$ready = $false
while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    $attempt++
}
if (-not $ready) {
    Write-Host "Фронтенд не ответил за 45 сек. Откройте вручную: http://localhost:5173" -ForegroundColor Yellow
}

Write-Host "Открываю http://localhost:5173 в браузере..." -ForegroundColor Green
Start-Process "http://localhost:5173"
Write-Host "Остановка: docker compose -f docker/docker-compose.yml down" -ForegroundColor Gray
