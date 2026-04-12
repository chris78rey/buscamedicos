# Script de Arranque Híbrido - BuscaMedicos
# DB en Docker + Backend/Frontend Local

Write-Host "--- Levantando Base de Datos en Docker ---" -ForegroundColor Cyan
cd infra
docker-compose up -d postgres
cd ..

# Configuración del Backend
$backendDir = "g:\codex_projects\buscamedicos\backend_api"
$envVarsBackend = @{
    "DATABASE_URL" = "postgresql+asyncpg://buscamedicos:buscamedicos123@localhost:5432/buscamedicos"
    "SECRET_KEY" = "dev-secret-key-buscamedicos"
}

# Configuración del Frontend
$frontendDir = "g:\codex_projects\buscamedicos\web_frontend"
$envVarsFrontend = @{
    "NUXT_PUBLIC_API_BASE" = "http://localhost:8000/api/v1"
}

Write-Host "--- Lanzando Backend en ventana independiente ---" -ForegroundColor Green
$backendCommand = "cd '$backendDir'; if (!(Test-Path .venv)) { Write-Host 'Creando entorno virtual...'; python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; `$env:DATABASE_URL='postgresql+asyncpg://buscamedicos:buscamedicos123@localhost:5432/buscamedicos'; `$env:SECRET_KEY='dev-secret-key-buscamedicos'; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

Write-Host "--- Lanzando Frontend en ventana independiente ---" -ForegroundColor Yellow
$frontendCommand = "cd '$frontendDir'; if (!(Test-Path node_modules)) { Write-Host 'Instalando node_modules...'; npm install }; `$env:NUXT_PUBLIC_API_BASE='http://localhost:8000/api/v1'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "--- Todo el sistema está arrancando ---" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
