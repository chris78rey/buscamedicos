# Reset Docker to PostgreSQL only - desarrollo local rápido
# Detiene backend, seed y frontend en Docker - solo deja PostgreSQL corriendo

param(
    [switch]$SkipConfirmation
)

$ErrorActionPreference = "Stop"

Write-Host "=== Fase 1: Reset a solo PostgreSQL ===" -ForegroundColor Cyan
Write-Host "Este script deja solo PostgreSQL corriendo en Docker." -ForegroundColor Yellow
Write-Host ""

if (-not $SkipConfirmation) {
    $confirm = Read-Host "¿Continuar? (s/n)"
    if ($confirm -ne "s") {
        Write-Host "Operación cancelada." -ForegroundColor Red
        exit 0
    }
}

# 1. Apagar el stack completo si está corriendo
Write-Host "[1/4] Apagando stack completo..." -ForegroundColor Yellow
docker compose -f .\docker-compose.yml down --remove-orphans 2>$null

# 2. Detener y eliminar backend, seed y frontend en Docker
Write-Host "[2/4] Eliminando contenedores de backend y frontend..." -ForegroundColor Yellow
$containersToRemove = @("buscamedicos_backend", "buscamedicos_backend_seed", "buscamedicos_web_frontend")
foreach ($container in $containersToRemove) {
    $running = docker ps -q -f "name=$container"
    if ($running) {
        Write-Host "  Deteniendo $container..." -ForegroundColor Gray
        docker stop $container 2>$null
    }
    $exists = docker ps -a -q -f "name=$container"
    if ($exists) {
        docker rm -f $container 2>$null | Out-Null
    }
}

# 3. Limpiar basura de Docker (sin tocar volúmenes)
Write-Host "[3/4] Limpiando recursos huérfanos..." -ForegroundColor Yellow
docker system prune -f --volumes=false 2>$null

# 4. Verificar que PostgreSQL esté corriendo
Write-Host "[4/4] Verificando PostgreSQL..." -ForegroundColor Yellow
$postgresRunning = docker ps -q -f "name=buscamedicos_postgres"
if ($postgresRunning) {
    Write-Host "  PostgreSQL está corriendo" -ForegroundColor Green
} else {
    Write-Host "  Levantando PostgreSQL..." -ForegroundColor Yellow
    docker compose -f .\docker-compose.dev-db-only.yml up -d
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "=== Resultado ===" -ForegroundColor Cyan
docker ps -a --filter "name=buscamedicos"

Write-Host ""
Write-Host "Para verificar DB:" -ForegroundColor Cyan
Write-Host "  docker exec -it buscamedicos_postgres pg_isready -U buscamedicos -d buscamedicos" -ForegroundColor Gray
Write-Host ""
Write-Host "Para revertir al stack completo:" -ForegroundColor Cyan
Write-Host "  docker compose -f .\docker-compose.dev-db-only.yml down" -ForegroundColor Gray
Write-Host "  docker compose -f .\docker-compose.yml up -d" -ForegroundColor Gray
