Sí. La forma más rápida para ver cambios es usar un esquema **híbrido**:

* **base de datos sola** en Docker;
* **backend** fuera de Docker con `uvicorn --reload`;
* **frontend** fuera de Docker con `npm run dev`.

El propio proyecto ya contempla correr el backend **fuera de Docker** con:

```bash
cd backend_api
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

y usa Docker Compose solo como flujo alterno de desarrollo.

---

#### Impacto y riesgos

Ventajas de este enfoque:

* los cambios en Python se reflejan mucho más rápido;
* los cambios en Nuxt se ven casi instantáneamente;
* Docker deja de reconstruirse a cada rato;
* la RAM queda más libre porque no corre todo dentro de contenedores.

Riesgos controlados:

* hay que tener Python y Node instalados localmente;
* la base de datos debe seguir disponible;
* si se mezclan puertos ocupados, puede haber conflicto.

---

#### Preparación

La configuración mínima recomendada es esta:

* **PostgreSQL**: en Docker o instalado local;
* **Backend**: local;
* **Frontend**: local.

Si se quiere dejar solo la base de datos en Docker, primero bajar todo el compose actual:

```bash
cd infra
docker compose down --remove-orphans
```

Luego levantar **solo postgres**.

Si el `docker-compose.yml` no tiene perfiles por servicio fáciles de usar, lo más simple por ahora es correr un postgres suelto:

```bash
docker run -d \
  --name buscamedicos_postgres_dev \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=buscamedicos \
  -p 5432:5432 \
  postgres:16
```

Con eso Docker queda usando solo la BD.

---

#### Fase 1

**Objetivo**
Levantar backend local con recarga automática.

**Riesgo controlado**
No se toca código, solo forma de ejecución.

**Archivo a revisar**

* `.env` del backend o variables de entorno;
* conexión a base de datos.

**Comandos**

```bash
cd backend_api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Eso ya está alineado con la forma oficial de desarrollo local del proyecto.

**Cómo probar**

```bash
curl http://localhost:8000/health/live
```

Debe responder con estado OK. El proyecto usa ese health check como referencia.

**Qué debe seguir funcionando**

* endpoints FastAPI;
* migraciones;
* seed manual si hace falta.

**Cómo revertir esa fase**
Cerrar `uvicorn` y volver al compose cuando se quiera.

---

#### Prueba de Fase 1

Cambiar cualquier texto pequeño en un router o servicio y guardar.
`uvicorn --reload` debe reiniciar solo el backend en segundos.

---

#### Fase 2

**Objetivo**
Levantar frontend local con hot reload real.

**Riesgo controlado**
No se toca backend ni DB.

**Archivo a revisar**

* `web_frontend/nuxt.config.ts`
* variable `NUXT_PUBLIC_API_BASE`

**Comandos**

```bash
cd web_frontend
npm install
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

Así el frontend queda apuntando al backend local en puerto 8000.

**Cómo probar**
Abrir:

```bash
http://localhost:3000
```

Cambiar cualquier texto en una página `.vue` y guardar.
Nuxt debe reflejar el cambio casi inmediato.

**Qué debe seguir funcionando**

* login;
* navegación por rol;
* llamadas al backend con `/api/v1`.

**Cómo revertir**
Cerrar `npm run dev`.

---

#### Prueba de Fase 2

Modificar un texto en `web_frontend/pages/professional/agenda.vue` y guardar.
El cambio debe verse mucho más rápido que con Docker Compose.

---

#### Fase 3

**Objetivo**
Dejar un flujo diario simple para trabajar rápido y usar Docker Compose solo al final.

**Riesgo controlado**
No cambia arquitectura, solo rutina de trabajo.

**Flujo recomendado diario**

**Base de datos**

```bash
docker start buscamedicos_postgres_dev
```

**Backend**

```bash
cd backend_api
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd web_frontend
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 npm run dev
```

**Al final, antes de validar integración completa**

```bash
cd infra
docker compose --profile required up -d
```

Eso sirve para la prueba final de “todo junto”, pero no para desarrollar cada cambio.

---

#### Prueba de Fase 3

Se recomienda esta secuencia:

1. desarrollar local;
2. validar feature;
3. recién al final correr compose;
4. hacer smoke test manual.

---

#### Pruebas de regresión

Cuando un bloque quede listo:

```bash
cd backend_api
pytest tests/ -v
```

Y luego:

```bash
cd infra
docker compose --profile required up -d
```

Eso confirma que lo desarrollado rápido fuera de Docker sigue funcionando dentro del stack final. El proyecto también contempla esa separación entre desarrollo local y Docker dev.

---

#### Plan de reversión total

Si se quisiera volver al modo anterior:

```bash
pkill -f uvicorn
pkill -f "npm run dev"
cd infra
docker compose --profile required up -d
```

---

### Recomendación más práctica

La mejor configuración para avanzar rápido sería esta:

* **Docker solo para PostgreSQL**
* **FastAPI local con `uvicorn --reload`**
* **Nuxt local con `npm run dev`**
* **Docker Compose solo al final para validar integración**

Eso da la velocidad que se está buscando sin romper la forma final de despliegue del proyecto.

Si se quiere, en el siguiente mensaje se puede dejar un script único tipo:

* `dev_db_only.sh`
* `dev_backend_local.sh`
* `dev_front_local.sh`

para arrancar todo más cómodo.
