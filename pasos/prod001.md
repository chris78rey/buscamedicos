Se revisó el arranque local y los puntos que ya fallaron, más los archivos que con alta probabilidad van a romper el siguiente paso. La idea más segura para el programador sería tocar solo estos archivos y no abrir una refactorización más grande.

### Bloqueantes ya confirmados

1. **`infra/docker-compose.yml`**
   El compose local quedó inconsistente con el `README`: el `README` manda usar `docker compose --profile required up -d`, pero el compose local tiene un bloque raíz `profiles:` inválido y además usa rutas relativas `./backend_api`, mientras el compose productivo usa `../backend_api`, lo que encaja con la ubicación real del archivo dentro de `infra`. El cambio mínimo sería:

   * eliminar el bloque raíz `profiles:`
   * cambiar `build.context: ./backend_api` por `../backend_api`
   * cambiar `./backend_api:/app` por `../backend_api:/app`
   * dejar `version:` solo si se quiere, aunque ya no aporta nada y Compose la marca como obsoleta.   

2. **`backend_api/alembic.ini`**
   Ese archivo está mal formado para `fileConfig(...)`: tiene `[handlers]` y `[formatters]` vacíos y termina con un `[keys]` suelto. Por eso ya se produjo el `KeyError: 'keys'`. El cambio mínimo sería corregir solo la sección de logging de Alembic; no hace falta tocar `env.py` si se arregla bien `alembic.ini`. 

3. **`backend_api/app/models/role.py`**
   Ese archivo usa `datetime.utcnow` en `created_at` y `assigned_at`, pero no importa `datetime`. El cambio mínimo es agregar `from datetime import datetime`. 

4. **`backend_api/app/models/system.py`**
   Ahí existe una definición legacy de `ExceptionalAccessRequest` con `__tablename__ = "exceptional_access_requests"`. El paso 7 también define esa misma tabla en `step7_models.py`, que es la versión nueva y más completa. El cambio mínimo sería eliminar del archivo `system.py` la clase legacy `ExceptionalAccessRequest` y su enum `ExceptionalAccessStatus`, dejando ahí solo `SystemParameter`, `FeatureFlag` y `EntityVersion`.   

5. **`backend_api/app/models/__init__.py`**
   Ese archivo importa `ExceptionalAccessRequest` primero desde `system.py` y luego otra vez desde `step7_models.py`. Aunque en Python el nombre final termine “pisado”, SQLAlchemy ya vio ambas clases y por eso apareció el error de tabla duplicada. El cambio mínimo sería quitar del `__init__.py` la importación de `ExceptionalAccessRequest` y `ExceptionalAccessStatus` desde `system.py`, y dejar la importación de acceso excepcional solo desde `step7_models.py`. 

### Archivos que probablemente van a romper después del fix anterior

6. **`backend_api/app/routers/access_control.py`**
   Ese router sigue importando `ExceptionalAccessRequest` y `ExceptionalAccessStatus` desde `app.models.system`. Si se elimina la clase legacy de `system.py`, ese router se rompe al importar. El cambio mínimo sería uno de estos dos:

   * migrarlo al modelo/servicio nuevo del paso 7, o
   * deshabilitarlo temporalmente si quedó obsoleto frente al flujo de privacidad nuevo.
     Mantenerlo apuntando al modelo viejo ya no es consistente con el paso 7.  

7. **`backend_api/app/routers/__init__.py`** y **`backend_api/app/main.py`**
   El paquete de routers importa `privacy_auditor_router` desde `.privacy_auditor`, pero en la estructura del repositorio no aparece `backend_api/app/routers/privacy_auditor.py`. Además `app.main` incluye ese router. Si no existe ese archivo, el backend va a fallar al arrancar aunque ya pasen las migraciones. El cambio mínimo sería:

   * crear `backend_api/app/routers/privacy_auditor.py`, o
   * quitar temporalmente su import y su `include_router` hasta que exista.   

8. **`backend_api/scripts/seed.py`**
   El script importa `FeatureFlag as FF` desde `app.models.step2_models`, pero `FeatureFlag` está definido en `app.models.system.py`, no en `step2_models.py`. Cuando llegue el momento de correr `python scripts/seed.py`, eso va a fallar. El cambio mínimo sería corregir esa línea a `from app.models.system import FeatureFlag as FF` o simplemente usar `FeatureFlag` desde `app.models`.  

### Riesgo alto de fallos funcionales después del arranque

9. **`backend_api/app/models/audit.py`**, **`backend_api/app/services/step6_services.py`**, **`backend_api/app/services/step7_services.py`** y **`backend_api/app/routers/ops.py`**
   Aquí hay una inconsistencia seria de contrato.
   El modelo `AuditEvent` define campos como `actor_user_id`, `entity_type`, `entity_id`, `before_json`, `after_json` y `justification`. Pero los servicios y routers lo están instanciando con nombres distintos como `user_id`, `resource_type`, `resource_id`, `metadata_json`, `details_json`, `operational_scope` y `release_code`. Además la migración `007_step8.py` sí agrega `operational_scope` y `release_code` a `audit_events`, pero el ORM actual no los refleja. Eso no impide la migración, pero sí va a romper flujos de moderación, privacidad y ops cuando se ejecuten. El cambio mínimo y coherente sería:

   * alinear el ORM `AuditEvent` con la migración `007`
   * elegir un solo contrato de nombres y ajustar los call sites de `step6_services.py`, `step7_services.py` y `ops.py` a ese contrato.
     Aquí no conviene parchear a medias, porque la inconsistencia ya está en varios lugares.     

### Orden sugerido para que el programador no toque de más

1. `infra/docker-compose.yml`
2. `backend_api/alembic.ini`
3. `backend_api/app/models/role.py`
4. `backend_api/app/models/system.py`
5. `backend_api/app/models/__init__.py`
6. `backend_api/app/routers/access_control.py`
7. `backend_api/app/routers/__init__.py` y `backend_api/app/main.py` o creación de `backend_api/app/routers/privacy_auditor.py`
8. `backend_api/scripts/seed.py`
9. bloque de auditoría: `backend_api/app/models/audit.py`, `backend_api/app/services/step6_services.py`, `backend_api/app/services/step7_services.py`, `backend_api/app/routers/ops.py`

### Texto corto para pasarle al programador

Se detectaron bloqueantes concretos para levantar local y correr migraciones: compose local inconsistente, `alembic.ini` inválido, `role.py` sin import de `datetime`, duplicidad de `exceptional_access_requests` entre `system.py` y `step7_models.py`, `__init__.py` importando ambas definiciones, router `access_control.py` aún atado al modelo viejo, referencia a `privacy_auditor.py` sin archivo visible, `seed.py` importando `FeatureFlag` desde el módulo equivocado y contrato inconsistente de `AuditEvent` entre ORM, servicios y ops. Se recomienda corregir solo esos archivos, en ese orden, sin tocar lógica de negocio adicional.         

Si se desea, se puede dejar en el siguiente mensaje un **checklist exacto de diff por archivo**, línea por línea, para que el programador aplique solo cambios mínimos.
