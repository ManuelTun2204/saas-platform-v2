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

# ============================================
# BANCO DE IMÁGENES POR INDUSTRIA (Unsplash - GRATIS y HD)
# ============================================
INDUSTRY_IMAGES = {
    "pasteleria": {
        "hero": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?w=600&q=80",
            "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=600&q=80",
            "https://images.unsplash.com/photo-1535141192574-577bf8821c5f?w=600&q=80",
            "https://images.unsplash.com/photo-1562440499-64c9a111f713?w=600&q=80",
            "https://images.unsplash.com/photo-1587668178277-295251f900ce?w=600&q=80",
            "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=600&q=80",
            "https://images.unsplash.com/photo-1542826435-b99d325e0c48?w=600&q=80",
            "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=600&q=80"
        ]
    },
    "reposteria": {
        "hero": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?w=600&q=80",
            "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=600&q=80",
            "https://images.unsplash.com/photo-1535141192574-577bf8821c5f?w=600&q=80",
            "https://images.unsplash.com/photo-1562440499-64c9a111f713?w=600&q=80",
            "https://images.unsplash.com/photo-1587668178277-295251f900ce?w=600&q=80",
            "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=600&q=80",
            "https://images.unsplash.com/photo-1542826435-b99d325e0c48?w=600&q=80",
            "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=600&q=80"
        ]
    },
    "restaurante": {
        "hero": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1504642723647-d623a4006d02?w=600&q=80",
            "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&q=80",
            "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=600&q=80",
            "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80",
            "https://images.unsplash.com/photo-1551218808-94e220e084d2?w=600&q=80",
            "https://images.unsplash.com/photo-1559847844-5315695dadae?w=600&q=80",
            "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&q=80",
            "https://images.unsplash.com/photo-1424847651672-bf20a4b0982b?w=600&q=80"
        ]
    },
    "tecnologia": {
        "hero": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&q=80",
            "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600&q=80",
            "https://images.unsplash.com/photo-1551434678-e076c223a692?w=600&q=80",
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1531233558888-9c4f3c5c4c5f?w=600&q=80"
        ]
    },
    "consultoria": {
        "hero": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?w=600&q=80",
            "https://images.unsplash.com/photo-1507672561168-30d1d1c079c6?w=600&q=80",
            "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=600&q=80",
            "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80"
        ]
    },
    "gimnasio": {
        "hero": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&q=80",
            "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=600&q=80",
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&q=80",
            "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=600&q=80",
            "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=600&q=80",
            "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=600&q=80",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600&q=80",
            "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=600&q=80"
        ]
    },
    "clinica": {
        "hero": "https://images.unsplash.com/photo-1519494123728-cf00c82424b5?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1519491050282-cf00c82424b5?w=600&q=80",
            "https://images.unsplash.com/photo-1551076805-e1869033e5cc?w=600&q=80",
            "https://images.unsplash.com/photo-1584982751601-97dcc096659c?w=600&q=80",
            "https://images.unsplash.com/photo-1631815583675-b20c6c30b455?w=600&q=80",
            "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600&q=80",
            "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=600&q=80",
            "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600&q=80",
            "https://images.unsplash.com/photo-1629909613654-28e377c36b09?w=600&q=80"
        ]
    },
    "default": {
        "hero": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920&q=80",
        "about": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&q=80",
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=600&q=80",
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600&q=80",
            "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&q=80",
            "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=600&q=80",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&q=80",
            "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&q=80",
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&q=80"
        ]
    }
}

# ============================================
# MAPEO DE ICONOS EMOJI → FONTAWESOME
# ============================================
ICON_MAPPING = {
    "🎂": "fa-birthday-cake", "🍰": "fa-birthday-cake", "🧁": "fa-birthday-cake",
    "⭐": "fa-star", "🌟": "fa-star", "✨": "fa-star",
    "💼": "fa-briefcase", "🛠️": "fa-tools", "🔧": "fa-wrench",
    "🎨": "fa-palette", "📱": "fa-mobile-alt", "💻": "fa-laptop",
    "🏆": "fa-trophy", "🚀": "fa-rocket", "💡": "fa-lightbulb",
    "📞": "fa-phone", "📧": "fa-envelope", "🏠": "fa-home",
    "🎯": "fa-bullseye", "💰": "fa-dollar-sign", "❤️": "fa-heart",
    "⚡": "fa-bolt", "🍞": "fa-bread-slice", "☕": "fa-coffee",
    "🍫": "fa-cookie-bite", "🎉": "fa-glass-cheers", "👰": "fa-heart",
    "🏋️": "fa-dumbbell", "💪": "fa-dumbbell", "🏥": "fa-heartbeat",
    "🦷": "fa-tooth", "👁️": "fa-eye", "🚗": "fa-car", "✈️": "fa-plane"
}


def detect_industry_key(industry: str) -> str:
    """Detecta la categoría de industria para asignar imágenes"""
    industry_lower = industry.lower()
    
    # Normalizar acentos
    industry_normalized = industry_lower.replace("í", "i").replace("é", "e").replace("á", "a")
    
    keywords_map = {
        "pasteleria": ["pastel", "pasteleria", "reposteria", "cake", "bakery", "panaderia", "dulce", "cupcake"],
        "restaurante": ["restaurante", "comida", "food", "cafe", "bar", "pizzeria", "taqueria"],
        "tecnologia": ["tecnologia", "software", "tech", "it", "desarrollo", "app", "web"],
        "consultoria": ["consultoria", "consultor", "asesoria", "coaching", "finanzas", "legal", "abogado"],
        "gimnasio": ["gimnasio", "gym", "fitness", "deporte", "entrenamiento", "yoga"],
        "clinica": ["clinica", "medico", "doctor", "salud", "dental", "dentista", "estetica", "spa"]
    }
    
    for category, keywords in keywords_map.items():
        if any(keyword in industry_normalized for keyword in keywords):
            return category
    
    return "default"


def map_icons(services: list) -> list:
    """Convierte iconos emoji a FontAwesome"""
    for service in services:
        original_icon = service.get("icon", "⭐")
        service["icon"] = ICON_MAPPING.get(original_icon, "fa-star")
    return services


class WebsiteService:
    def __init__(self):
        self.llm_service = LLMService()

    def _save_tenant_info(self, tenant_id: str, package: str, deliverables: list):
        """Guarda información del tenant en tenants.json"""
        tenant_info = {
            "id": tenant_id,
            "package": package,
            "deliverables": deliverables,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        tenants_file = DATA_DIR / "tenants.json"
        tenants = []
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                try:
                    tenants = json.load(f)
                except:
                    pass
        tenants = [t for t in tenants if t.get("id") != tenant_id]
        tenants.append(tenant_info)
        with open(tenants_file, 'w', encoding='utf-8-sig') as f:
            json.dump(tenants, f, indent=2, ensure_ascii=False)

    def _render_site(self, template_name: str, site_data: dict, seo_enabled: bool, chatbot_enabled: bool) -> str:
        """Renderiza el sitio web con imágenes dinámicas"""
        dummy_request = Request(scope={"type": "http", "method": "GET", "headers": [], "path": "/"})
        
        # Detectar industria y asignar imágenes
        industry_key = detect_industry_key(site_data.get("industry", ""))
        images = INDUSTRY_IMAGES.get(industry_key, INDUSTRY_IMAGES["default"])
        
        # Enriquecer site_data con imágenes y configuración
        site_data["seo_enabled"] = seo_enabled
        site_data["chatbot_enabled"] = chatbot_enabled
        site_data["hero_image"] = images["hero"]
        site_data["about_image"] = images["about"]
        site_data["gallery_images"] = images["gallery"]
        
        # Mapear iconos a FontAwesome
        site_data["services"] = map_icons(site_data.get("services", []))
        
        # Renderizar template
        return templates.get_template(template_name).render(request=dummy_request, **site_data)

    async def generate_modular_service(self, tenant_id: str, industry: str, objective: str, audience: str, tone: str, package: str, brand_hex: str = "#2563eb", brand_secondary: str = "#764ba2", visual_style: str = "modern", calendly_url: str = "", contact_email: str = "", contact_phone: str = "", contact_address: str = "") -> dict:
        logger.info(f"🚀 Procesando paquete: {package} para {tenant_id}")

        # Generar contenido con IA
        site_data = await self.llm_service.generate_website_json(industry, objective, audience, tone, visual_style)
        site_data["tenant_id"] = tenant_id
        site_data["cache_buster"] = int(time.time())
        site_data["industry"] = industry
        site_data["brand_hex"] = brand_hex
        site_data["brand_secondary"] = brand_secondary
        site_data["calendly_url"] = calendly_url
        site_data["contact_email"] = contact_email
        site_data["contact_phone"] = contact_phone
        site_data["contact_address"] = contact_address

        deliverables = []
        preview_url = "#"

        try:
            if package == "full":
                logger.info("Ejecutando: SERVICIO COMPLETO")
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                
                html_content = self._render_site(template_name, site_data, seo_enabled=True, chatbot_enabled=True)
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional con Imágenes HD", "Chatbot RAG Integrado", "Optimización SEO Completa"]

            elif package == "web_chat":
                logger.info("Ejecutando: WEB + CHATBOT")
                template_name = "services.html" if "servicio" in industry.lower() else "landing.html"
                
                html_content = self._render_site(template_name, site_data, seo_enabled=False, chatbot_enabled=True)
                
                tenant_dir = WEBSITES_DIR / tenant_id
                tenant_dir.mkdir(exist_ok=True)
                with open(tenant_dir / "index.html", "w", encoding="utf-8-sig") as f:
                    f.write(html_content)
                
                preview_url = f"/data/websites/{tenant_id}/index.html?v={site_data['cache_buster']}"
                deliverables = ["Sitio Web Profesional con Imágenes HD", "Chatbot RAG Integrado"]

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
                Devuelve SOLO un objeto JSON válido (sin markdown) con esta estructura:
                {{
                    "meta_title": "Título SEO (máx 60 chars)",
                    "meta_description": "Descripción (máx 155 chars)",
                    "primary_keyword": "keyword principal",
                    "secondary_keywords": ["kw1", "kw2", "kw3"],
                    "schema_json_ld": {{"@context": "https://schema.org", "@type": "LocalBusiness", "name": "{industry}"}},
                    "seo_recommendations": ["Rec 1", "Rec 2", "Rec 3"]
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
                        "meta_description": f"Expertos en {industry}. {objective}. Contáctanos hoy.",
                        "primary_keyword": industry.lower(),
                        "secondary_keywords": [f"{industry} profesional", "mejor servicio", "consultoría especializada"],
                        "schema_json_ld": {"@context": "https://schema.org", "@type": "LocalBusiness", "name": industry},
                        "seo_recommendations": [
                            "Crea una sección de Preguntas Frecuentes (FAQ).",
                            "Registra tu negocio en Google Business Profile.",
                            "Solicita reseñas a tus clientes."
                        ]
                    }
                
                schema_string = json.dumps(seo_data.get("schema_json_ld", {}), indent=2, ensure_ascii=False)
                
                seo_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte SEO | {industry}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style> body {{ font-family: 'Inter', sans-serif; }} </style>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen p-8">
    <div class="max-w-5xl mx-auto">
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">📈 Reporte SEO Profesional</h1>
            <p class="text-gray-600">Industria: {industry} | Objetivo: {objective}</p>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">🏷️ Meta Tags Optimizados</h2>
            <div class="bg-gray-50 p-4 rounded-lg mb-3">
                <p class="text-sm font-semibold text-gray-700">Título SEO:</p>
                <p class="text-blue-600 text-lg">{seo_data.get('meta_title', 'N/A')}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
                <p class="text-sm font-semibold text-gray-700">Meta Description:</p>
                <p class="text-gray-700">{seo_data.get('meta_description', 'N/A')}</p>
            </div>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">🔧 Schema Markup (JSON-LD)</h2>
            <pre class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-x-auto">{schema_string}</pre>
        </div>
        <div class="bg-white rounded-2xl shadow-xl p-8">
            <h2 class="text-2xl font-bold mb-4">💡 Recomendaciones</h2>
            {''.join([f'<div class="flex gap-3 p-4 bg-gray-50 rounded-lg mb-2"><span>✅</span><p>{rec}</p></div>' for rec in seo_data.get('seo_recommendations', [])])}
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

            self._save_tenant_info(tenant_id, package, deliverables)

            logger.info(f"✅ PROCESO EXITOSO: Paquete '{package}' generado para '{tenant_id}'")
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "package": package,
                "deliverables": deliverables,
                "preview_url": preview_url,
                "site_data": site_data
            }

        except Exception as e:
            logger.error(f"❌ FALLO CRÍTICO en paquete '{package}': {str(e)}", exc_info=True)
            raise Exception(f"Error interno generando el paquete {package}: {str(e)}")