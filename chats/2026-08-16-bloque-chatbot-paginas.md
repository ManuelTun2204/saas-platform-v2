# Bloque 6 — Chatbot para páginas existentes (2026-08-16)

Objetivo: reforzar el producto **"Solo Chatbot"** (paquete chat_only). Hay clientes
que ya tienen su página y solo quieren comprar el chatbot para agregarlo a su sitio.
Antes era un producto secundario; ahora es un producto de primera clase: el widget
se instala con **una sola línea** y su apariencia/mensajes se controlan desde el panel.

## Qué se hizo

### A. Configuración del widget por tenant (nuevo)
- **Nuevo servicio** `services/chat_config_service.py`:
  - Config por tenant guardada en `data/storage/chat_configs.json` (escritura atómica).
  - `default_chat_config(tenant_id)`: arma defaults a partir del nombre de la empresa
    (título "Asistente de {Empresa}", saludo con el nombre, colores #667eea/#764ba2,
    quick replies genéricas). Si el tenant no existe, usa defaults genéricos.
  - `get_chat_config()` = defaults + lo guardado por el admin (la config del admin gana).
  - `_clean_config()`: valida y normaliza (título ≤80, subtítulo ≤120, bienvenida ≤400,
    máx. 4 respuestas rápidas de 60 caracteres).
  - `build_widget_snippet()`: genera el código de instalación de una sola línea.
- **Endpoints** en `tenants.py`:
  - `GET /api/chat/{tenant_id}/config` **público** (sin login): lo usa el widget al
    instalarse; devuelve `config` + `api_base`.
  - `GET /api/chat-config/{tenant_id}` (admin): la misma config para editar.
  - `POST /api/chat-config/{tenant_id}` (admin): guarda la config. Acepta
    `quick_replies` como lista o como texto separado por comas.
- `schemas.py`: nuevo `ChatConfigRequest` (campos + `quick_replies: Union[List[str], str]`).

### B. Widget instalable con una línea (`widget.js`)
- El widget ahora se lee **atributos `data-*`** del propio `<script>`:
  `<script src=".../static/widget/widget.js" data-tenant="mi-empresa"></script>`.
  También siguen funcionando las variables `CHATBOT_TENANT_ID`, `CHATBOT_TITLE`, etc.
- Si hay un tenant, el widget **descarga su configuración sola** (`GET /api/chat/{id}/config`)
  y aplica título, subtítulo, colores, avatar, bienvenida y respuestas rápidas sin tocar el HTML.
- Precedencia: lo que pone el cliente con atributos/variables gana sobre la config del panel
  (permite personalización extra). Si no hay red/config, usa defaults y no rompe nada.
- Refactor: el gradiente pasó de constante a función `grad()` y `applyConfig()` actualiza
  en vivo el fondo del botón/header/enviar, el título, el subtítulo y el avatar.
- **CORS**: el backend ya permitía `*` (cualquier origen), así el widget funciona en la
  página del cliente aunque sea otro dominio.

### C. Panel admin — "Chatbot para tu Pagina"
- La sección del chatbot ahora muestra el snippet de **una sola línea** (con `data-tenant`).
- Nueva zona **"Personalizar Chatbot"**: título, subtítulo, color principal, color
  secundario, mensaje de bienvenida y respuestas rápidas (máx 4, separadas por coma).
  Guardar → `POST /api/chat-config/{id}`; al guardar recarga la vista previa.
- El botón "Copiar Codigo" copia el snippet. Los sitios generados por la plataforma
  también usan la config del panel (antes solo el tenant_id; ahora el widget la carga).

### D. Entrega del paquete chat_only
- `website_service.py`: el código de instalación que se entrega es el **snippet de una
  línea** (antes eran dos líneas con variable). La página `chatbot-install.html` mantiene
  los 3 pasos (copiar → pegar antes de `</body>` → listo) y la **vista previa en vivo**
  con el widget ya embebido, que ahora aplica la config del panel.

## Probado en vivo
- Config pública sin token: devuelve defaults con nombre de la empresa ("Asistente de
  Vet Dog S.A.").
- Guardar config personalizada (título, colores verdes, bienvenida, 3 quick replies) →
  la pública la devuelve igual; `quick_replies` acepta string separado por comas.
- Generación chat_only → `chatbot-install.html` con el snippet de una línea en el cuadro
  de copia y como script embebido en la vista previa.
- Widget servido en `/static/widget/widget.js` (200 OK) con el nuevo código.
- **Test headless del widget (Node + DOM simulado)**: se detectó y corrigió un bug — el
  backend manda claves `snake_case` (`primary_color`) y el widget esperaba `camelCase`;
  ahora hay un mapeo explícito. Test final: título, subtítulo y gradiente aplicados
  correctamente desde la config remota (PASS).
- CORS `*` confirmado (el widget funciona en dominios externos).

## Commit
`141166e` — feat: bloque chatbot paginas (6 archivos, +325/-25), subido a GitHub (`main`).
Anterior: `f927596` (charla bloque atractivo).

## Notas / pendientes
- El flujo de compra (checkout → pago → entrega) ya soporta el paquete chat_only; la
  entrega es la página `chatbot-install.html` con el snippet.
- Para que el bot responda con datos reales, el cliente (o el admin) sube documentos en
  "Entrenar Chatbot" (ya existía).
- Sigue pendiente la deuda técnica: Postgres y contenedores huérfanos (`saas-postgres`,
  `saas-n8n`, `saas-postiz`, `saas-typebot-*`).
