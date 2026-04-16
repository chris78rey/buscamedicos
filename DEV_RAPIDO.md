# Desarrollo Rápido - BuscaMedicos

## Concepto

Mantener **solo PostgreSQL en Docker**, ejecutar **FastAPI y Nuxt en el host** con hot-reload para detección inmediata de cambios.

**Antes (lento):**
- Cada cambio en `.py` o `.vue` requería rebuild de contenedor Docker
- Tiempos de espera de 30-60 segundos

**Ahora (rápido):**
- Cambios en archivos se detectan instantáneamente
- Backend recarda en ~1 segundo
- Frontend hot-reload en ~2 segundos

## Preparación (una vez)

### 1. Asegúrate de que Docker Desktop esté corriendo

### 2. Aplica Fase 1 (solo PostgreSQL en Docker)

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\dev_reset_to_db_only.ps1
```

### 3. Inicia desarrollo rápido

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\dev_fast_start.ps1 -ForceInstall
```

La primera vez installa dependencias Python y Node.js. Las siguientes veces es instantáneo.

## Flujo de Desarrollo

### Iniciar (cada día)

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\dev_fast_start.ps1
```

### Detener

Cierra las dos ventanas de PowerShell que se abrieron.

### Verificar que todo funciona

```powershell
# Health check backend
curl http://127.0.0.1:8000/health/live

# Ver logs backend (en la ventana de PowerShell del backend)
# Solo reinicia el proceso si algo falla
```

### Cambios que debes ver reflejados al guardar

| Tipo | Archivo | Detección |
|------|---------|-----------|
| Backend Python | `backend_api/app/**/*.py` | ~1 seg |
| Frontend Vue | `web_frontend/**/*.vue` | ~2 seg |
| Frontend JS | `web_frontend/**/*.js` | ~2 seg |

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  Tu Computadora (Host)                                  │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐                     │
│  │ FastAPI     │    │ Nuxt 4      │                     │
│  │ localhost   │    │ localhost   │                     │
│  │ :8000       │    │ :3000       │                     │
│  └──────┬──────┘    └──────┬──────┘                     │
│         │                   │                           │
│         │   ┌───────────────┘                           │
│         │   │                                           │
│         ▼   ▼                                           │
│  ┌─────────────┐    ┌─────────────────────────────┐     │
│  │ Python      │    │ package.json scripts       │     │
│  │ requirements│    │ (dev: `npm run dev`)       │     │
│  └─────────────┘    └─────────────────────────────┘     │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Docker Desktop                                      │ │
│  │                                                     │ │
│  │  ┌──────────────────┐                               │ │
│  │  │ PostgreSQL 16    │  ← SOLO ESTE CONTENEDOR      │ │
│  │  │ buscamedicos_    │                               │ │
│  │  │ postgres         │                               │ │
│  │  └──────────────────┘                               │ │
│  │                                                     │ │
│  │  localhost:5432 → PostgreSQL                        │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Archivos del Proyecto

### Nuevos archivos

| Archivo | Propósito |
|---------|-----------|
| `infra/docker-compose.dev-db-only.yml` | Solo PostgreSQL |
| `infra/scripts/dev_reset_to_db_only.ps1` | Reset a modo DB-only |
| `infra/scripts/dev_fast_start.ps1` | Inicia backend+frontend local |
| `DEV_RAPIDO.md` | Este documento |

### Archivos NO tocados

- `infra/docker-compose.yml` - Se mantiene intacto
- `backend_api/` - Lógica funcional sin cambios
- `web_frontend/` - Frontend sin cambios

## Rutas de Archivos

### Antes (en Docker)

```
backend_api:/app/files  →  files_data volume
```

### Ahora (desarrollo local)

```
backend_api/files/  →  Directorio local en tu máquina
```

El script `dev_fast_start.ps1` crea `backend_api/files/` automáticamente.

## Revertir a Modo Docker Completo

### Opción 1: Solo detener desarrollo local

1. Cierra las ventanas de PowerShell del backend y frontend
2. (Opcional) Levanta el stack completo si lo necesitas:

```powershell
docker compose -f .\infra\docker-compose.yml up -d
```

### Opción 2: Reversión total (repo como antes)

```powershell
# 1. Detener todo
docker compose -f .\infra\docker-compose.dev-db-only.yml down

# 2. Volver al stack completo
docker compose -f .\infra\docker-compose.yml up -d

# 3. Borrar los archivos nuevos
Remove-Item infra\docker-compose.dev-db-only.yml
Remove-Item infra\scripts\dev_reset_to_db_only.ps1
Remove-Item infra\scripts\dev_fast_start.ps1
Remove-Item DEV_RAPIDO.md
```

## Pruebas de Regression

Después de cambiar a desarrollo local, verifica:

- [ ] `curl http://127.0.0.1:8000/health/live` → `{"status":"ok"}`
- [ ] Login de usuario existente
- [ ] Registro de nuevo usuario
- [ ] Navegación por pantallas protegidas
- [ ] CRUD de registros desde frontend
- [ ] Subida de archivos (PDF, imágenes)
- [ ] Persistencia de datos después de reiniciar

## Troubleshooting

### "Backend no conecta a PostgreSQL"

```powershell
docker exec -it buscamedicos_postgres pg_isready -U buscamedicos -d buscamedicos
```

Si no responde, ejecutar:
```powershell
docker compose -f .\infra\docker-compose.dev-db-only.yml restart
```

### "Node modules faltantes en frontend"

```powershell
cd web_frontend
npm install
```

### "pip modules faltantes en backend"

```powershell
cd backend_api
.\venv\Scripts\pip install -r requirements.txt
```

### "Puerto ya en uso"

Verifica que no tengas otro proceso en los puertos:

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5432
```

## Notas

- El backend usa `PYTHONPATH` apuntando a `backend_api/`
- La URL de la base de datos se construye automáticamente desde `infra/.env`
- Los cambios en `.env` requieren reiniciar el backend (cierra y abre la ventana)
