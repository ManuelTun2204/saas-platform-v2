# Charla: Analisis del proyecto y mejoras aplicadas

**Fecha:** 2026-08-14
**Proyecto:** saas-platform-v2

---

## Que se pidio

Analizar el proyecto (lo ultimo que se habia hecho fue afinar el dashboard) y buscar mejoras.

## Hallazgos

### Bugs encontrados (arreglados en el commit c5a53cd)

1. **El chatbot no usaba los datos de cada empresa.** El backend guardaba los tenants en
   `data/tenants.json`, pero el chatbot leia `data/storage/tenants.json` (archivo distinto y vacio).
   Resultado: el `system_prompt` y el nombre de cada empresa no llegaban al chatbot.
   **Arreglo:** `storage_service.py` ahora apunta la coleccion `tenants` a `data/tenants.json`.

2. **Leads del chatbot no aparecian en la grafica del dashboard.** El chatbot guardaba el lead con
   el campo `captured_at`, pero la grafica "Leads ultimos 7 dias" lee `timestamp`.
   **Arreglo:** unificado en `timestamp`.

### Mejoras al dashboard aplicadas

- Ingresos estimados ahora solo cuentan empresas con pago confirmado (`payment_status = paid`).
- Graficas con estado vacio ("Sin datos aun") en vez de quedar en blanco.
- Nueva seccion "Ultimos Leads" (email, empresa, pregunta y fecha de los 10 mas recientes).
- Boton "Actualizar" para recargar las metricas sin recargar la pagina.
- Nueva metrica `paid_tenants` (empresas pagadas) disponible en el API.

### Pendientes detectados (no implementados)

- Subir PDFs: la interfaz permite .pdf pero el backend solo indexa .txt (falta usar pypdf).
- `main.py` tiene 1030 lineas: separar en routers.
- Carpetas `app/` y `frontend/` en la raiz son versiones viejas sin usar.
- No hay pruebas automatizadas de la API.

## Archivos modificados

- `backend/app/services/storage_service.py`
- `backend/app/services/rag_service.py`
- `backend/app/main.py`
- `backend/app/static/admin/index.html`

## Nota

Los commits de esta charla ya estan en GitHub (rama main). Para traerlos a la PC de la oficina
hacer pull (doble clic en SINCRONIZAR.cmd) y reconstruir el backend:
`docker compose up -d --build backend`.
