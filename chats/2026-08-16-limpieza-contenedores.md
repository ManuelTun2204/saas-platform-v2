# Bloque 7 — Limpieza de contenedores huérfanos y deuda técnica (2026-08-16)

Objetivo: liberar recursos y eliminar servicios experimentales que se habían quedado
corriendo y no usa la plataforma. El único servicio real es `saas-backend` (el compose
se quedó limpio).

## Qué se encontró

Contenedores huérfanos (no estaban en docker-compose.yml, eran experimentos previos):
- `saas-n8n` (n8n): en bucle de reinicio por error (`Encryption key missing`), y su
  carpeta de datos `n8n_data/` estaba VACÍA (sin workflows).
- `saas-postiz` (programación de redes sociales): sin volúmenes de datos.
- `saas-typebot-builder` y `saas-typebot-viewer` (constructor de chatbots): sin volúmenes.
- `saas-postgres` (Postgres **15**, distinto del servicio `db` del compose que es 16):
  usaba el volumen `saas-platform-v2_postgres_data` (84 MB de datos de prueba).
- `hungry_haibt` (imagen vieja `chatbot-platform-backend`): parado desde hace 2 semanas.

Dato clave: **la app NO usa Postgres**. El backend no tiene librerías SQL
(no hay sqlalchemy/psycopg) y todo el almacenamiento es por archivos JSON
(`data/tenants.json`, `data/storage/*.json`). El servicio `db` del compose y las
variables `DB_*/DATABASE_URL` del `.env` son configuración muerta de un plan de
migración que nunca se hizo.

## Qué se hizo

1. **Contenedores eliminados** (decisión del usuario): `saas-n8n`, `saas-postiz`,
   `saas-typebot-builder`, `saas-typebot-viewer`, `saas-postgres`, `hungry_haibt`.
2. **Volumen de datos borrado**: `saas-platform-v2_postgres_data` (datos del Postgres
   15 de prueba; la plataforma no guarda nada ahí).
3. **Carpeta `n8n_data/` eliminada** (estaba vacía).
4. **Imagen vieja eliminada**: `chatbot-platform-backend:latest`.
5. **Prune de volúmenes anónimos huérfanos** (7 volúmenes sin dueño) e imágenes sin
   etiqueta. Los volúmenes de OTRO proyecto (`metricool_postgres_data`,
   `metricool_redis_data`) se dejaron intactos.
6. **Config Postgres conservada** (decisión del usuario): el servicio `db` del compose
   y las variables `DB_*/DATABASE_URL` del `.env` quedan como estaban, por si algún
   día se decide migrar a una base de datos.

## Estado final

- `docker ps`: solo `saas-backend` (API en localhost:8000).
- `docker compose ps`: solo `backend`; ya NO aparece el aviso de "orphan containers".
- API verificada: login admin OK.
- No se tocó docker-compose.yml ni .env (decisión de conservar la config Postgres).

## Notas / pendientes
- La "deuda técnica" de Postgres queda documentada: si se quiere migrar algún día,
  hay que convertir el almacenamiento JSON (tenants, leads, conversations, orders,
  llm_usage, chat_configs) a tablas y añadir las librerías al backend. A la escala
  actual los archivos JSON funcionan bien y son más simples.
- Pendiente de revisión aparte: la carpeta `C:\projects\metricool` (otro proyecto)
  tiene sus propios contenedores/volúmenes; no se tocó.
