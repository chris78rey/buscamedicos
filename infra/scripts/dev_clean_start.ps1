# Script de limpieza y arranque seguro para BuscaMedicos en Windows
Write-Host "--- Iniciando limpieza de Docker ---" -ForegroundColor Cyan

# Apagar servicios eliminando huérfanos
docker-compose -f infra/docker-compose.yml down --remove-orphans

# Limpiar contenedores detenidos, imágenes no usadas y cachés de build
# NOTA: Esto NO borra los volúmenes (la base de datos y archivos están seguros)
docker system prune -af
docker builder prune -af

Write-Host "--- Levantando servicios esenciales (Perfil: required) ---" -ForegroundColor Green
docker-compose -f infra/docker-compose.yml --profile required up -d

Write-Host "--- Docker está limpio y corriendo ---" -ForegroundColor Cyan
docker ps -a
