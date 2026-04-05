# Reglas de Autorización

## Principio Fundamental

Los administradores NUNCA pueden acceder a datos clínicos directamente.
Todo acceso a datos sensibles debe ser auditado.

## Roles y Permisos

### super_admin
- Gestiona usuarios y configuración del sistema
- NO puede ver datos clínicos (future: acceso excepcional auditado)
- Puede gestionar roles

### admin_validation
- Revisa documentos de profesionales
- Aprueba o rechaza solicitudes de verificación
- NO puede ver datos clínicos

### admin_support
- Acceso a datos no clínicos para soporte
- NO puede ver datos clínicos

### patient
- Solo puede acceder a su propia información
- No puede acceder a información de otros usuarios

### professional
- Solo puede gestionar su propio perfil y documentos
- No puede aprobarse a sí mismo

## Control Contextual

Además del rol, se verifica:
1. `is_owner` - ¿El usuario es dueño del recurso?
2. `has_relationship` - ¿Existe relación válida con el recurso?
3. `is_non_clinical_admin_action` - ¿La acción es administrativa no clínica?
4. `requires_justification` - ¿La acción requiere justificación documentada?

## Middleware de Autorización

```python
require_role(allowed_roles: List[str])
require_owner_or_role(resource_owner_id: str, allowed_roles: List[str])
require_non_clinical_admin_scope()
```

## Casos de Prueba

1. Patient no puede acceder a endpoints admin
2. Professional no puede aprobarse a sí mismo
3. Admin_validation no puede leer datos clínicos
4. Todo acceso genera audit_event