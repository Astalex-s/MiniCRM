# Запуск CRM API в Docker одной командой.
# Из корня проекта: .\docker\run.ps1   или из любой папки: .\docker\run.ps1
# Требуется: Docker Engine
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot
docker compose -f docker/docker-compose.yml up --build
