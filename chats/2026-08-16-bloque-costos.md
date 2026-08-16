# Bloque 4 — Costos (LLM barato vía OpenRouter) (2026-08-16)

Objetivo: reducir y controlar el gasto de IA del SaaS usando modelos Qwen3 baratos
vía OpenRouter (ya se tenía la clave), en lugar del llama-3.1-8b anterior.

## Decisión de modelos (probado en vivo)

Se probaron varios modelos Qwen3 contra el prompt REAL de generación de sitio:
- `qwen/qwen3.7-flash` → descartado: devuelve 1200+ tokens pero contenido vacío
  (modelo tipo "thinking" que no responde en el campo `content`).
- `qwen/qwen3-coder-30b-a3b-instruct` → JSON válido (mejor adherencia JSON).
- `qwen/qwen3-next-80b-a3b-instruct` → JSON válido (mejor calidad, salida más cara: $1.10/M).
- `qwen/qwen3-30b-a3b-instruct-2507` → **GANADOR**: JSON completo válido al primer
  intento (12 campos, 6 servicios, 3 testimonios, 3 precios), español excelente.

Precios (entrada/salida por 1M tokens): llama-3.1-8b $0.05/$0.08 ·
qwen3-30b-a3b $0.05/$0.19 · coder-30b $0.07/$0.28 · next-80b $0.10/$1.10.

## Qué se hizo

1. **Modelos configurables por variable de entorno** (`llm_service.py`):
   - `LLM_SITE_MODEL` (def. `qwen/qwen3-30b-a3b-instruct-2507`): generación de sitios.
   - `LLM_CHAT_MODEL` (def. `qwen/qwen3-30b-a3b-instruct-2507`): respuestas del chatbot.
   - `LLM_FALLBACK_MODEL` (def. `meta-llama/llama-3.1-8b-instruct`): se usa si el principal falla.
   - `generate_content` ahora acepta `model`, valida respuesta vacía y hace fallback automático.

2. **Registro de costos por llamada** (`_log_cost`):
   - Lee `usage_metadata` de la respuesta (tokens entrada/salida).
   - Calcula costo estimado con tabla de precios por modelo (MODEL_PRICES).
   - Loguea en consola: `LLM <modelo>: X tokens entrada, Y salida, costo ~$Z USD`.
   - Persiste cada llamada en `data/storage/llm_usage.json` (atómico, máx 10000 registros).

3. **Dashboard admin — "Costo IA (mes)"**:
   - Nueva métrica roja en el resumen (junto a Ingresos).
   - Nueva gráfica "Costo IA por Mes (LLM via OpenRouter)" (últimos 6 meses).
   - `analytics.py` ahora devuelve: `llm_cost_this_month`, `llm_cost_total`,
     `llm_calls_total`, `llm_calls_this_month` y chart `llm_cost_monthly`.

4. **Logs de la app visibles en docker logs**: `main.py` agrega
   `logging.basicConfig(level=logging.INFO)`. Antes uvicorn descartaba los INFO de la app;
   ahora se ven costos de IA, errores, etc.

5. **Variables añadidas a `.env` y `docker-compose.yml`** con defaults, para cambiar
   de modelo sin tocar código.

## Costos reales medidos

- Generación de un sitio web completo (paquete web_chat): 1456 in + 1772 out ≈ **$0.00041 USD**.
- Un mensaje del chatbot: 138-179 in + 20 out ≈ **$0.00001 USD**.
- Referencia: los clientes pagan $249 por paquete Web + Chat; el costo de IA por sitio
  es despreciable (centésimas de centavo).

## Archivos modificados
- `backend/app/services/llm_service.py`
- `backend/app/routers/analytics.py`
- `backend/app/static/admin/index.html`
- `backend/app/main.py`
- `docker-compose.yml`
- `.env` (gitignored)

## Pruebas realizadas (Docker)
- Generación de sitio con Qwen: JSON completo válido, site generado, costo registrado.
- Chat con Qwen: responde bien, costo registrado.
- Línea de costo visible en `docker logs saas-backend`.
- Analytics devuelve métricas de costo correctas y chart mensual.
- Datos de prueba limpiados (JSONs en `[]`, solo queda `admin/admin123`).

## Siguiente paso opcional (fuera del SaaS)
Configurar un subagente barato (Qwen3 via OpenRouter) en opencode para tareas simples
del desarrollo, y así también reducir el costo de las sesiones de trabajo.
