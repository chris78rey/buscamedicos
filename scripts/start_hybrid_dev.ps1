param (
    [switch]$ForceInstall = $false
)

# Script de Arranque Híbrido Optimizado - BuscaMedicos
Write-Host "--- Levantando Base de Datos en Docker ---" -ForegroundColor Cyan
cd infra
docker-compose up -d postgres
cd ..

# Configuración del Backend
$backendDir = "$PSScriptRoot\..\backend_api"
Write-Host "--- Lanzando Backend (FastAPI) ---" -ForegroundColor Green

$backendCommand = @"
cd '$backendDir'
if ('$ForceInstall' -eq 'True' -or !(Test-Path .venv)) {
    Write-Host 'Preparando entorno virtual y dependencias...' -ForegroundColor Cyan
    if (!(Test-Path .venv)) { python -m venv .venv }
    .\.venv\Scripts\activate
    pip install -r requirements.txt
} else {
    .\.venv\Scripts\activate
}
`$env:DATABASE_URL='postgresql+asyncpg://buscamedicos:buscamedicos123@localhost:5432/buscamedicos'
`$env:SECRET_KEY='dev-secret-key-buscamedicos'
Write-Host 'Iniciando Uvicorn con Auto-Reload...' -ForegroundColor Green
uvicorn app.main:app --reload --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# Configuración del Frontend
$frontendDir = "$PSScriptRoot\..\web_frontend"
Write-Host "--- Lanzando Frontend (Nuxt/Vite) ---" -ForegroundColor Yellow

$frontendCommand = @"
cd '$frontendDir'
if ('$ForceInstall' -eq 'True' -or !(Test-Path node_modules)) {
    Write-Host 'Instalando dependencias de Node (esto puede tardar)...' -ForegroundColor Cyan
    npm install
}
`$env:NUXT_PUBLIC_API_BASE='http://localhost:8000/api/v1'
Write-Host 'Iniciando Nuxt con HMR (Hot Module Replacement)...' -ForegroundColor Yellow
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "--- Sistema Híbrido Listo ---" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Usa el flag -ForceInstall si añades nuevas librerías al proyecto."
