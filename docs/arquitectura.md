# Arquitectura BuscaMedicos

## Visión General

Plataforma marketplace de salud en Ecuador que conecta pacientes con profesionales de salud validados.

## Stack Tecnológico

- **Frontend**: Flutter + Dart
- **Backend**: FastAPI + Python 3.11
- **Base de Datos**: PostgreSQL 16
- **Cache/Colas**: Redis (opcional en paso 1)
- **Contenedores**: Docker Compose

## Arquitectura del Backend

Monolito modular con domains:
- `auth` - Autenticación JWT
- `users` - Gestión de usuarios
- `people` - Datos personales
- `patients` - Perfiles de pacientes
- `professionals` - Perfiles de profesionales
- `verification` - Solicitudes de validación
- `agreements` - Términos y aceptaciones
- `audit` - Registro de auditoría
- `access_control` - Control de acceso excepciones
- `files` - Almacenamiento de archivos

## Seguridad

### Roles
- `super_admin` - Admin total (sin acceso clínico por defecto)
- `admin_validation` - Revisa documentos de profesionales
- `admin_support` - Acceso soporte no clínico
- `patient` - Paciente
- `professional` - Profesional de salud

### Principios
1. RBAC + Control contextual
2. Soft delete en todos los registros críticos
3. Versionado de entidades
4. Auditoría de operaciones críticas
5. Acceso clínico prohibido para admins (preparado para futuro)