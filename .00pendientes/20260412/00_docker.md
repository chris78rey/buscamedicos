Sí. Para dejar Docker **mínimo, limpio y predecible** en un equipo de desarrollo, conviene aplicar una configuración conservadora en tres capas:

1. limitar qué servicios arrancan;
2. evitar acumulación de basura;
3. limpiar automáticamente al reiniciar.

A continuación se deja una propuesta pequeña y segura.

#### Impacto y riesgos

Esta configuración busca:

* que Docker no consuma RAM innecesaria;
* que no queden contenedores viejos, redes huérfanas y cachés creciendo;
* que, tras reiniciar el equipo, el entorno vuelva “liviano”.

Riesgos controlados:

* si se limpia demasiado agresivo, se pueden borrar imágenes o cachés que luego tocará reconstruir;
* no se deben borrar volúmenes si contienen base de datos que se quiera conservar;
* por eso aquí se propone **limpieza sin tocar volúmenes**.

---

#### Preparación

Primero conviene revisar cuánto está consumiendo Docker ahora:

```bash
docker stats --no-stream
docker system df
docker ps -a
docker images
docker network ls
docker volume ls
```

Si se quiere conservar el estado actual antes de limpiar:

```bash
docker compose -f infra/docker-compose.yml ps
docker image ls > /tmp/docker_images_before.txt
docker ps -a > /tmp/docker_ps_before.txt
docker system df > /tmp/docker_df_before.txt
```

---

#### Fase 1

**Objetivo**
Dejar el `docker-compose` lo más pequeño posible para desarrollo local.

**Riesgo controlado**
Solo se arranca lo necesario.

**Archivo a tocar**
`infra/docker-compose.yml`

**Qué se recomienda**

* levantar solo backend + postgres;
* no dejar servicios opcionales corriendo;
* usar `restart: unless-stopped` solo en lo indispensable;
* agregar límites suaves de logging para que no crezcan los JSON logs.

En cada servicio, añadir este bloque si no existe:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

Eso evita que los logs se acumulen demasiado.

Si el compose tiene servicios no esenciales para la prueba diaria, conviene dejarlos bajo perfiles y arrancar solo lo mínimo con:

```bash
docker compose -f infra/docker-compose.yml --profile required up -d
```

Ese patrón ya está alineado con la documentación del proyecto. 

**Cómo probar**

```bash
docker compose -f infra/docker-compose.yml --profile required up -d
docker stats --no-stream
```

**Qué debe seguir funcionando**

* backend;
* postgres;
* health check del backend.

**Cómo revertir**
Quitar solo el bloque `logging` si diera algún problema.

---

#### Prueba de Fase 1

Comprobar:

```bash
curl http://localhost:8000/health/live
docker stats --no-stream
```

El backend debe responder `{"status":"ok"}` y el consumo debe verse estable.

---

#### Fase 2

**Objetivo**
Evitar residuos de ejecuciones anteriores.

**Riesgo controlado**
Se limpian contenedores detenidos, redes huérfanas e imágenes no usadas, pero **sin borrar volúmenes**.

**Configuración operativa recomendada**

En vez de usar siempre `up -d`, conviene usar este ciclo:

**para apagar limpio:**

```bash
docker compose -f infra/docker-compose.yml down --remove-orphans
```

**para volver a levantar:**

```bash
docker compose -f infra/docker-compose.yml --profile required up -d
```

**para limpiar residuos después de bajar:**

```bash
docker system prune -af
docker builder prune -af
```

Importante: aquí **no** se usa `--volumes`.

Si se quiere una sola secuencia manual segura:

```bash
docker compose -f infra/docker-compose.yml down --remove-orphans && docker system prune -af && docker builder prune -af
```

Eso deja la memoria y el disco bastante limpios antes del siguiente arranque.

**Cómo probar**

```bash
docker compose -f infra/docker-compose.yml down --remove-orphans
docker system df
```

Debe bajar la basura de contenedores detenidos, cachés y redes no usadas.

**Qué debe seguir funcionando**

* al volver a levantar, el entorno debe reconstruirse normal;
* la base de datos debe seguir existiendo si está en volumen nombrado y no se borró el volumen.

**Cómo revertir**
No hay cambio permanente todavía; solo dejar de correr el prune.

---

#### Fase 3

**Objetivo**
Hacer que, tras cada reinicio del equipo, Docker quede liviano automáticamente.

**Riesgo controlado**
Se ejecuta una limpieza segura al arrancar el sistema.

**Archivo a crear**
`/usr/local/bin/docker-clean-safe.sh`

**Código exacto**

```bash
#!/usr/bin/env bash
set -e

/usr/bin/docker container prune -f
/usr/bin/docker image prune -af
/usr/bin/docker network prune -f
/usr/bin/docker builder prune -af
```

Dar permisos:

```bash
sudo chmod +x /usr/local/bin/docker-clean-safe.sh
```

Luego crear este servicio systemd.

**Archivo a crear**
`/etc/systemd/system/docker-clean-safe.service`

**Contenido exacto**

```ini
[Unit]
Description=Safe Docker cleanup after boot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-clean-safe.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable docker-clean-safe.service
```

Con eso, cada vez que el equipo arranque, Docker limpiará residuos seguros.

**Qué limpia**

* contenedores detenidos;
* imágenes no usadas;
* redes no usadas;
* cache de build.

**Qué no limpia**

* volúmenes.

Eso protege la base de datos local.

---

#### Prueba de Fase 2

Se puede ejecutar manualmente una vez:

```bash
sudo systemctl start docker-clean-safe.service
docker system df
```

Y luego reiniciar el equipo para verificar que arranque limpio.

---

#### Pruebas de regresión

Después de aplicar todo:

1. reiniciar el equipo;
2. comprobar que Docker sube sin residuos pesados;
3. verificar:

```bash
docker system df
docker ps -a
docker stats --no-stream
```

4. levantar de nuevo el proyecto:

```bash
docker compose -f infra/docker-compose.yml --profile required up -d
```

5. validar backend:

```bash
curl http://localhost:8000/health/live
```

---

#### Plan de reversión total

Si se quiere volver al estado anterior:

```bash
sudo systemctl disable docker-clean-safe.service
sudo rm -f /etc/systemd/system/docker-clean-safe.service
sudo rm -f /usr/local/bin/docker-clean-safe.sh
sudo systemctl daemon-reload
```

Y simplemente dejar de usar `prune` manual.

---

### Configuración mínima recomendada

Si se quisiera solo lo esencial, sin tocar demasiadas cosas, la versión más simple sería esta:

**1. En compose, limitar logs**

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**2. Para apagar siempre limpio**

```bash
docker compose -f infra/docker-compose.yml down --remove-orphans
```

**3. Para limpiar residuos sin borrar BD**

```bash
docker system prune -af
docker builder prune -af
```

**4. Para arrancar solo lo mínimo**

```bash
docker compose -f infra/docker-compose.yml --profile required up -d
```

Si se quiere, en el siguiente mensaje se puede dejar un `infra/scripts/dev_reset_light.sh` listo para pegar y ejecutar con un solo comando.
