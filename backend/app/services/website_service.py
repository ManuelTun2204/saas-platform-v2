import os, json, logging, time
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR.parent / "data"
WEBSITES_DIR = DATA_DIR / "websites"
WEBSITES_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

class WebsiteService:
    def __init__(self):
        self.llm_service = LLMService()

    async def generate_modular_service(self, tenant_id: str, industry: str, objective: str, audience: str, tone: str, package: str, brand_hex: str = "#2563eb", brand_secondary: str = "#764ba2", visual_style: str = "modern", calendly_url: str = "", contact_email: str = "", contact_phone: str = "", contact_address: str = "") -> dict:
        logger.info(f"🚀 Procesando paquete: {package} para {tenant_id}")
        
        # Pedimos a la IA que también genere preguntas frecuentes para SEO
        site_data = await self.llm_service.generate_website_json(industry, objective, audience, tone, visual_style)
        site_data["tenant_id"] = tenant_id
        site_data["cache_buster"] = int(time.time())
        
        deliverables = []
        preview_url = "#"

        try:
            if package == "full":
                logger.info("Ejecutando: SERVICIO COMPLETO")
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                dummy_request = Request(scope={"type": "http", "method": "GET", "headers": [], "path": "/"})
                
                site_data["seo_enabled"] = True
                html_content = templates.get_template(template_name).render(request=dummy_request, **site_data)
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional", "Chatbot RAG Integrado", "Optimización SEO Completa (incl. FAQ)"]

            elif package == "web_chat":
                logger.info("Ejecutando: WEB + CHATBOT")
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                dummy_request = Request(scope={"type": "http", "method": "GET", "headers": [], "path": "/"})
                
                site_data["seo_enabled"] = False
                html_content = templates.get_template(template_name).render(request=dummy_request, **site_data)
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional", "Chatbot RAG Integrado"]

            elif package == "chat_only":
                logger.info("Ejecutando: SOLO CHATBOT")
                widget_code = f"<script>\n  var CHATBOT_TENANT_ID = '{tenant_id}';\n</script>\n<script src=\"http://localhost:8000/static/widget/widget.js\"></script>"
                
                chat_html = f"""<!DOCTYPE html><html><head><title>Instalación Chatbot</title><script src="https://cdn.tailwindcss.com"></script></head>
                <body class="bg-gray-50 p-10 font-sans">
                    <div class="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-lg">
                        <h1 class="text-2xl font-bold mb-4">Tu Chatbot está listo</h1>
                        <p class="mb-4">Copia este código y pégalo en el &lt;body&gt; de tu sitio web actual:</p>
                        <textarea class="w-full h-32 p-3 bg-gray-100 border rounded font-mono text-sm" readonly>{widget_code}</textarea>
                        <p class="mt-4 text-green-600 font-semibold">✅ Widget activo para el tenant: {tenant_id}</p>
                    </div>
                </body></html>"""
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "chatbot-install.html", "w", encoding="utf-8-sig") as f:
                    f.write(chat_html)
                
                preview_url = f"/data/websites/{tenant_id}/chatbot-install.html"
                deliverables = ["Código del Widget de Chatbot", "Panel de Administración de Leads"]

            elif package == "seo_only":
                logger.info("Ejecutando: SOLO POSICIONAMIENTO (SEO)")
                seo_prompt = f"""
                Eres un experto en SEO técnico y posicionamiento en Google.
                Genera un reporte SEO completo y profesional para:
                - Industria: {industry}
                - Objetivo: {objective}
                - Audiencia: {audience}
                
                Devuelve SOLO un objeto JSON válido (sin markdown) con esta estructura exacta:
                {{
                    "meta_title": "Título SEO optimizado (máximo 60 caracteres, incluye palabra clave principal)",
                    "meta_description": "Descripción persuasiva (máximo 155 caracteres, incluye llamada a la acción)",
                    "primary_keyword": "Palabra clave principal (1-3 palabras)",
                    "secondary_keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"],
                    "schema_json_ld": {{
                        "@context": "https://schema.org",
                        "@type": "LocalBusiness",
                        "name": "{industry}",
                        "description": "Descripción del negocio enfocada en {objective}",
                        "address": {{
                            "@type": "PostalAddress",
                            "streetAddress": "Dirección completa",
                            "addressLocality": "Ciudad",
                            "addressRegion": "Estado",
                            "postalCode": "Código postal",
                            "addressCountry": "MX"
                        }},
                        "telephone": "+52-XXX-XXX-XXXX",
                        "openingHours": "Mo-Fr 09:00-18:00",
                        "priceRange": "$$"
                    }},
                    "seo_recommendations": [
                        "Crea una sección de Preguntas Frecuentes (FAQ) en tu web respondiendo las 3 dudas principales de tus clientes sobre {industry}.",
                        "Registra tu negocio en Google Business Profile y vincula este sitio web.",
                        "Solicita a tus primeros 5 clientes satisfechos que dejen una reseña de 5 estrellas mencionando '{primary_keyword}'."
                    ]
                }}
                """
                
                try:
                    seo_raw = await self.llm_service.generate_content(seo_prompt, max_tokens=1500)
                    seo_clean = seo_raw.replace("```json", "").replace("```", "").strip()
                    seo_data = json.loads(seo_clean)
                except Exception as e:
                    logger.warning(f"Error parseando SEO, usando fallback: {e}")
                    seo_data = {
                        "meta_title": f"{industry} | Soluciones Profesionales",
                        "meta_description": f"Expertos en {industry}. {objective}. Contáctanos hoy para una consulta gratuita.",
                        "primary_keyword": industry.lower(),
                        "secondary_keywords": [f"{industry} profesional", "mejor servicio", "consultoría especializada", "soluciones a medida", "experiencia garantizada"],
                        "schema_json_ld": {
                            "@context": "https://schema.org",
                            "@type": "LocalBusiness",
                            "name": industry,
                            "description": f"Servicios profesionales de {industry}",
                            "address": {"@type": "PostalAddress", "streetAddress": "Tu dirección aquí", "addressLocality": "Tu ciudad", "addressRegion": "Tu estado", "postalCode": "00000", "addressCountry": "MX"},
                            "telephone": "+52-XXX-XXX-XXXX",
                            "openingHours": "Mo-Fr 09:00-18:00",
                            "priceRange": "$$"
                        },
                        "seo_recommendations": [
                            "Crea una sección de Preguntas Frecuentes (FAQ) en tu web.",
                            "Registra tu negocio en Google Business Profile.",
                            "Solicita reseñas a tus clientes mencionando tu servicio principal."
                        ]
                    }
                
                schema_string = json.dumps(seo_data.get("schema_json_ld", {}), indent=2, ensure_ascii=False)
                
                seo_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte SEO Profesional | {industry}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style> body {{ font-family: 'Inter', sans-serif; }} </style>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen p-8">
    <div class="max-w-5xl mx-auto">
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <div class="flex items-center gap-4 mb-4">
                <div class="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center text-3xl">📈</div>
                <div>
                    <h1 class="text-3xl font-bold text-gray-900">Reporte SEO Profesional</h1>
                    <p class="text-gray-600">Optimización completa para posicionamiento en Google</p>
                </div>
            </div>
            <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <p class="text-sm text-blue-800"><strong>Industria:</strong> {industry} | <strong>Objetivo:</strong> {objective}</p>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span class="text-3xl">🏷️</span> Meta Tags Optimizados</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Título SEO (aparece en azul en Google)</label>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <p class="text-blue-600 text-lg font-medium">{seo_data.get('meta_title', 'N/A')}</p>
                        <p class="text-xs text-gray-500 mt-1">Máximo 60 caracteres | Actual: {len(seo_data.get('meta_title', ''))} caracteres</p>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Meta Description</label>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <p class="text-gray-700">{seo_data.get('meta_description', 'N/A')}</p>
                        <p class="text-xs text-gray-500 mt-1">Máximo 155 caracteres | Actual: {len(seo_data.get('meta_description', ''))} caracteres</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span class="text-3xl">🎯</span> Palabras Clave Estratégicas</h2>
            <div class="mb-4">
                <span class="inline-block bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-full font-semibold text-lg">{seo_data.get('primary_keyword', 'N/A')}</span>
                <span class="text-sm text-gray-500 ml-2">(Palabra Clave Principal)</span>
            </div>
            <div class="flex flex-wrap gap-2">
                {"".join([f'<span class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm border border-gray-200">{kw}</span>' for kw in seo_data.get('secondary_keywords', [])])}
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span class="text-3xl">🔧</span> Schema Markup (JSON-LD)</h2>
            <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded mb-4">
                <p class="text-sm text-yellow-800"><strong>¿Qué es esto?</strong> Código especial que le dice a Google exactamente qué es tu negocio. Al implementarlo, Google puede mostrar información enriquecida en las búsquedas: estrellas, horarios, dirección, etc., haciendo que destaques sobre tu competencia.</p>
            </div>
            <div class="relative">
                <button onclick="navigator.clipboard.writeText(document.getElementById('schema-code').innerText).then(() => alert('✅ Copiado'))" class="absolute top-2 right-2 bg-gray-700 text-white text-xs px-3 py-1 rounded hover:bg-gray-600 transition">Copiar</button>
                <pre id="schema-code" class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-x-auto">{schema_string}</pre>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span class="text-3xl">💡</span> Recomendaciones de Contenido</h2>
            <div class="space-y-3">
                {"".join([f'<div class="flex gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200"><span class="text-2xl">✅</span><p class="text-gray-700 flex-1">{rec}</p></div>' for rec in seo_data.get('seo_recommendations', [])])}
            </div>
        </div>

        <div class="text-center text-gray-600 text-sm">
            <p>Reporte generado por SaaS Platform V2 | {time.strftime('%d/%m/%Y')}</p>
        </div>
    </div>
</body>
</html>"""
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "seo-report.html", "w", encoding="utf-8-sig") as f:
                    f.write(seo_html)
                
                preview_url = f"/data/websites/{tenant_id}/seo-report.html"
                deliverables = ["Auditoría SEO Completa", "Meta Tags Optimizados", "Schema Markup (JSON-LD)", "Recomendaciones de Contenido"]

            tenant_info = {"id": tenant_id, "package": package, "deliverables": deliverables, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            tenants_file = DATA_DIR / "tenants.json"
            tenants = []
            if tenants_file.exists():
                with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                    try: tenants = json.load(f)
                    except: pass
            tenants = [t for t in tenants if t.get("id") != tenant_id]
            tenants.append(tenant_info)
            with open(tenants_file, 'w', encoding='utf-8-sig') as f:
                json.dump(tenants, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ PROCESO EXITOSO: Paquete '{package}' generado para '{tenant_id}'")
            return {"status": "success", "tenant_id": tenant_id, "package": package, "deliverables": deliverables, "preview_url": preview_url, "site_data": site_data}

        except Exception as e:
            logger.error(f"❌ FALLO CRÍTICO en paquete '{package}': {str(e)}", exc_info=True)
            raise Exception(f"Error interno generando el paquete {package}: {str(e)}")


