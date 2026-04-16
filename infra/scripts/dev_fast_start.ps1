# Start development environment: PostgreSQL (Docker) + Backend + Frontend (local)
# Backend y frontend corren en el host con hot-reload para desarrollo rápido

param(
    [switch]$ForceInstall  # Instala dependencias si no existen
)

$ErrorActionPreference = "Stop"

# Directorios (el script está en infra/scripts/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InfraDir = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $InfraDir
$BackendDir = Join-Path $ProjectRoot "backend_api"
$FrontendDir = Join-Path $ProjectRoot "web_frontend"
$EnvFile = Join-Path $InfraDir ".env"

Write-Host "=== Fase 2: Desarrollo Rápido Local ===" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "Docs API: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

# 1. Cargar credenciales desde .env
Write-Host "[1/6] Cargando configuración..." -ForegroundColor Yellow
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^(.+?)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    Write-Host "  Configuración cargada desde .env" -ForegroundColor Green
} else {
    Write-Host "  .env no encontrado, usando valores por defecto" -ForegroundColor Yellow
}

# 2. Asegurar que PostgreSQL esté corriendo
Write-Host "[2/6] Verificando PostgreSQL en Docker..." -ForegroundColor Yellow
$postgresRunning = docker ps -q -f "name=buscamedicos_postgres"
if (-not $postgresRunning) {
    Write-Host "  PostgreSQL no está corriendo, levantándolo..." -ForegroundColor Yellow
    docker compose -f "$InfraDir\docker-compose.dev-db-only.yml" up -d
    Start-Sleep -Seconds 5
}

# Verificar que la base acepta conexiones
$pgReady = docker exec buscamedicos_postgres pg_isready -U buscamedicos -d buscamedicos 2>$null
if ($pgReady -match "accepting connections") {
    Write-Host "  PostgreSQL OK" -ForegroundColor Green
} else {
    Write-Host "  ERROR: PostgreSQL no acepta conexiones" -ForegroundColor Red
    exit 1
}

# 3. Crear directorio de archivos si no existe
Write-Host "[3/6] Preparando directorio de archivos..." -ForegroundColor Yellow
$FilesDir = Join-Path $BackendDir "files"
if (-not (Test-Path $FilesDir)) {
    New-Item -ItemType Directory -Path $FilesDir | Out-Null
    Write-Host "  Directorio creado: $FilesDir" -ForegroundColor Green
} else {
    Write-Host "  Directorio ya existe: $FilesDir" -ForegroundColor Gray
}

# 4. Preparar backend (dependencias)
Write-Host "[4/6] Preparando backend..." -ForegroundColor Yellow
$BackendReady = Join-Path $BackendDir "venv"
$BackendReadyFile = Join-Path $BackendDir ".backend_ready"

if ($ForceInstall -or -not (Test-Path $BackendReadyFile)) {
    Push-Location $BackendDir
    try {
        if (-not (Test-Path "venv")) {
            Write-Host "  Creando virtualenv con Python 3.12..." -ForegroundColor Gray
            py -3.12 -m venv venv
        }
        
        Write-Host "  Instalando dependencias..." -ForegroundColor Gray
        & ".\venv\Scripts\pip" install -r requirements.txt --quiet
        
        # Marcar como listo
        "Ready" | Out-File -FilePath $BackendReadyFile -Encoding UTF8
        Write-Host "  Backend preparado" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  Backend ya preparado (skipping). Use -ForceInstall para reintalar." -ForegroundColor Gray
}

# 5. Iniciar backend con hot-reload
Write-Host "[5/6] Iniciando backend FastAPI..." -ForegroundColor Yellow
$BackendEnv = @{
    "DATABASE_URL" = "postgresql+asyncpg://${env:POSTGRES_USER}:${env:POSTGRES_PASSWORD}@localhost:5432/${env:POSTGRES_DB}"
    "SECRET_KEY" = $env:SECRET_KEY
    "FILES_PATH" = $FilesDir
    "MAX_FILE_SIZE_MB" = "10"
    "PYTHONPATH" = $BackendDir
}

# Construir el comando con env vars
$envCmd = $BackendEnv.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }
$backendCmd = ".\venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

Write-Host "  Comando: $backendCmd" -ForegroundColor Gray
Write-Host "  Abriendo nueva ventana..." -ForegroundColor Gray

# Crear script temporal para el backend
$backendScript = Join-Path $env:TEMP "bm_backend_run.ps1"
@"
`$ErrorActionPreference = "Continue"
Set-Location '$BackendDir'
`$env:PYTHONPATH = '$BackendDir'
`$env:DATABASE_URL = 'postgresql+asyncpg://${env:POSTGRES_USER}:${env:POSTGRES_PASSWORD}@localhost:5432/${env:POSTGRES_DB}'
`$env:SECRET_KEY = '$($env:SECRET_KEY)'
`$env:FILES_PATH = '$FilesDir'
`$env:MAX_FILE_SIZE_MB = '10'
.\venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@ | Out-File -FilePath $backendScript -Encoding UTF8

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$BackendDir'; `$env:PYTHONPATH = '$BackendDir'; `$env:DATABASE_URL = 'postgresql+asyncpg://${env:POSTGRES_USER}:${env:POSTGRES_PASSWORD}@localhost:5432/${env:POSTGRES_DB}'; `$env:SECRET_KEY = '$($env:SECRET_KEY)'; `$env:FILES_PATH = '$FilesDir'; .\venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

# 6. Iniciar frontend con hot-reload
Write-Host "[6/6] Iniciando frontend Nuxt..." -ForegroundColor Yellow

Write-Host "  Abriendo nueva ventana..." -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FrontendDir'; npm run dev"

Write-Host ""
Write-Host "=== Desarrollo rápido iniciado ===" -ForegroundColor Green
Write-Host ""
Write-Host "Espera ~10 segundos y verifica:" -ForegroundColor Cyan
Write-Host "  curl http://127.0.0.1:8000/health/live" -ForegroundColor Gray
Write-Host ""
Write-Host "Abre en navegador:" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Para detener: cierra las ventanas de PowerShell abiertas" -ForegroundColor Yellow
Write-Host "Para revertir: docker compose -f .\docker-compose.dev-db-only.yml down" -ForegroundColor Gray
