import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Precios aproximados en USD por 1M tokens (entrada, salida) para estimar costos en logs.
# Se mantienen manualmente; si el modelo no aparece, el log muestra solo los tokens.
MODEL_PRICES = {
    "qwen/qwen3-30b-a3b-instruct-2507": (0.05, 0.19),
    "qwen/qwen3-coder-30b-a3b-instruct": (0.07, 0.28),
    "qwen/qwen3-next-80b-a3b-instruct": (0.10, 1.10),
    "qwen/qwen3.7-flash": (0.03, 0.13),
    "meta-llama/llama-3.1-8b-instruct": (0.05, 0.08),
    "mistralai/mistral-7b-instruct:free": (0.0, 0.0),
}

USAGE_FILE = DATA_DIR / "storage" / "llm_usage.json"


def _atomic_append_usage(record: dict):
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if USAGE_FILE.exists():
            with open(USAGE_FILE, "r", encoding="utf-8-sig") as f:
                records = json.load(f)
        if not isinstance(records, list):
            records = []
        records.append(record)
        # Mantener acotado el archivo (una empresa pequeña no pasa de 10000 llamadas)
        if len(records) > 10000:
            records = records[-10000:]
        tmp = USAGE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8-sig") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        tmp.replace(USAGE_FILE)
    except Exception as e:
        logger.debug(f"No se pudo guardar uso de LLM: {e}")


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = "https://openrouter.ai/api/v1"
        # Modelos configurables por variable de entorno (bloque de costos):
        # Qwen3 baratos vía OpenRouter, excelentes en español y JSON.
        self.site_model = os.getenv("LLM_SITE_MODEL", "qwen/qwen3-30b-a3b-instruct-2507").strip()
        self.chat_model = os.getenv("LLM_CHAT_MODEL", "qwen/qwen3-30b-a3b-instruct-2507").strip()
        self.fallback_model = os.getenv("LLM_FALLBACK_MODEL", "meta-llama/llama-3.1-8b-instruct").strip()

        if not self.api_key or not self.api_key.startswith("sk-or-"):
            logger.warning("OPENROUTER_API_KEY no configurada o inválida.")

    def _get_llm(self, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        """Crea el cliente de chat para un modelo dado"""
        return ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=120
        )

    def _log_cost(self, model: str, usage):
        """Registra tokens usados y costo estimado en logs + archivo para el dashboard"""
        try:
            usage = usage or {}
            in_tok = int(usage.get("input_tokens") or 0)
            out_tok = int(usage.get("output_tokens") or 0)
            price = MODEL_PRICES.get(model)
            cost_usd = None
            if price:
                cost_usd = (in_tok * price[0] + out_tok * price[1]) / 1_000_000
                logger.info(f"LLM {model}: {in_tok} tokens entrada, {out_tok} salida, costo ~${cost_usd:.6f} USD")
            else:
                logger.info(f"LLM {model}: {in_tok} tokens entrada, {out_tok} salida (precio no registrado)")
            _atomic_append_usage({
                "ts": datetime.utcnow().isoformat(),
                "model": model,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost_usd": cost_usd
            })
        except Exception as e:
            logger.debug(f"No se pudo estimar costo de LLM: {e}")

    async def generate_content(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.7, model: str = None) -> str:
        """Genera texto libre basado en un prompt, con fallback automatico si el modelo principal falla"""
        model = model or self.chat_model
        try:
            llm = self._get_llm(model, temperature=temperature, max_tokens=max_tokens)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            self._log_cost(model, getattr(response, "usage_metadata", None))
            content = (response.content or "").strip()
            if not content:
                raise Exception("El modelo devolvio respuesta vacia")
            return content
        except Exception as e:
            logger.warning(f"Fallo LLM principal {model}: {e}. Usando fallback {self.fallback_model}")
            try:
                llm = self._get_llm(self.fallback_model, temperature=temperature, max_tokens=max_tokens)
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                self._log_cost(self.fallback_model, getattr(response, "usage_metadata", None))
                content = (response.content or "").strip()
                if not content:
                    raise Exception("El fallback devolvio respuesta vacia")
                return content
            except Exception as e2:
                logger.error(f"Error en generate_content (fallback): {e2}")
                raise Exception(f"Error generando contenido: {str(e2)}")

    async def generate_website_json(self, industry: str, objective: str, audience: str, tone: str, visual_style: str = "modern") -> dict:
        """Genera JSON estructurado completo para sitio web profesional con todos los bloques"""
        
        prompt = f"""Eres un experto diseñador web y copywriter profesional. Genera contenido completo y realista para un sitio web de alta calidad.

DATOS DE LA EMPRESA:
- Industria: {industry}
- Objetivo: {objective}
- Audiencia: {audience}
- Tono: {tone}
- Estilo visual: {visual_style}

Devuelve SOLO un objeto JSON válido (sin markdown, sin ```json, sin texto adicional) con esta estructura EXACTA:

{{
    "company_name": "Nombre creativo y memorable de la empresa",
    "hero_title": "Título principal impactante (máx 60 caracteres)",
    "hero_subtitle": "Subtítulo persuasivo que explique el valor (máx 120 caracteres)",
    "hero_cta": "Texto del botón principal (Ej: 'Cotiza ahora', 'Ver servicios')",
    "services": [
        {{"title": "Servicio 1", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}},
        {{"title": "Servicio 2", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}},
        {{"title": "Servicio 3", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}},
        {{"title": "Servicio 4", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}},
        {{"title": "Servicio 5", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}},
        {{"title": "Servicio 6", "description": "Descripción breve y atractiva (máx 100 caracteres)", "icon": "emoji relevante"}}
    ],
    "about_text": "Párrafo sobre la empresa (150-200 palabras, tono profesional y cercano)",
    "benefits": ["Beneficio 1", "Beneficio 2", "Beneficio 3", "Beneficio 4", "Beneficio 5", "Beneficio 6"],
    "stats": [
        {{"number": 150, "label": "Clientes Felices", "icon": "😊"}},
        {{"number": 10, "label": "Años de Experiencia", "icon": "🏆"}},
        {{"number": 500, "label": "Proyectos Completados", "icon": "✅"}},
        {{"number": 98, "label": "Satisfacción (%)", "icon": "⭐"}}
    ],
    "testimonials": [
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones elogiando el servicio", "rating": 5, "photo_prompt": "profesional mexicano sonriente retrato corporativo"}},
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones sobre la experiencia", "rating": 5, "photo_prompt": "mujer profesional latina sonriente retrato"}},
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones recomendando el servicio", "rating": 4, "photo_prompt": "hombre de negocios profesional retrato corporativo"}}
    ],
    "pricing": [
        {{"name": "Básico", "price": "$99", "period": "/mes", "popular": false, "features": ["Característica básica 1", "Característica básica 2", "Característica básica 3", "Soporte por email"]}},
        {{"name": "Profesional", "price": "$199", "period": "/mes", "popular": true, "features": ["Todo del Básico", "Característica premium 1", "Característica premium 2", "Soporte prioritario"]}},
        {{"name": "Enterprise", "price": "$399", "period": "/mes", "popular": false, "features": ["Todo del Profesional", "Característica enterprise 1", "Característica enterprise 2", "Soporte 24/7 dedicado"]}}
    ],
    "team": [
        {{"name": "Nombre completo hispano", "role": "CEO / Fundador", "bio": "Breve descripción profesional de 1-2 oraciones"}},
        {{"name": "Nombre completo hispano", "role": "Director de Operaciones", "bio": "Breve descripción profesional de 1-2 oraciones"}},
        {{"name": "Nombre completo hispano", "role": "Especialista Principal", "bio": "Breve descripción profesional de 1-2 oraciones"}},
        {{"name": "Nombre completo hispano", "role": "Atención al Cliente", "bio": "Breve descripción profesional de 1-2 oraciones"}}
    ],
    "faqs": [
        {{"question": "¿Pregunta frecuente relevante para {industry}?", "answer": "Respuesta clara y útil de 2-3 oraciones"}},
        {{"question": "¿Pregunta sobre precios o costos?", "answer": "Respuesta clara y útil de 2-3 oraciones"}},
        {{"question": "¿Pregunta sobre tiempos de entrega?", "answer": "Respuesta clara y útil de 2-3 oraciones"}},
        {{"question": "¿Pregunta sobre garantías o calidad?", "answer": "Respuesta clara y útil de 2-3 oraciones"}},
        {{"question": "¿Pregunta sobre formas de pago?", "answer": "Respuesta clara y útil de 2-3 oraciones"}},
        {{"question": "¿Pregunta sobre atención al cliente?", "answer": "Respuesta clara y útil de 2-3 oraciones"}}
    ],
    "social_media": {{
        "facebook": "https://facebook.com/nombre-empresa",
        "instagram": "https://instagram.com/nombre-empresa",
        "tiktok": "https://tiktok.com/@nombre-empresa",
        "youtube": "",
        "twitter": ""
    }}
}}

REGLAS IMPORTANTES:
1. Los testimonios deben sonar NATURALES y auténticos, no genéricos
2. Los precios deben ser REALISTAS para la industria {industry}
3. Las FAQs deben ser preguntas REALES que haría un cliente
4. El equipo debe tener nombres HISPANOS variados (hombres y mujeres)
5. Todo el contenido debe estar en ESPAÑOL
6. Los números en 'stats' deben ser realistas para una empresa establecida
7. Devuelve SOLO el JSON, sin texto adicional, sin markdown, sin comentarios"""

        try:
            raw_response = await self.generate_content(prompt, max_tokens=3000, temperature=0.7, model=self.site_model)
            
            # Limpiar markdown si viene
            cleaned = raw_response.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            cleaned = cleaned.strip()
            
            # Intentar parsear
            try:
                result = json.loads(cleaned)
                logger.info(f"✅ JSON generado exitosamente para {industry}")
                return result
            except json.JSONDecodeError:
                # Intentar extraer JSON del texto
                match = re.search(r'\{[\s\S]*\}', cleaned)
                if match:
                    result = json.loads(match.group())
                    logger.info(f"✅ JSON extraído y parseado para {industry}")
                    return result
                raise
                
        except Exception as e:
            logger.error(f"Error generando/parseando JSON: {e}")
            logger.info("Usando datos de respaldo (fallback)")
            return self._get_fallback_data(industry)
    
    def _get_fallback_data(self, industry: str) -> dict:
        """Datos de respaldo completos si la IA falla"""
        return {
            "company_name": f"{industry.title()} Pro",
            "hero_title": f"Soluciones profesionales en {industry}",
            "hero_subtitle": f"Ofrecemos los mejores servicios de {industry} con calidad garantizada y atención personalizada",
            "hero_cta": "Contáctanos ahora",
            "services": [
                {"title": "Servicio Principal", "description": "Nuestro servicio más solicitado y de mayor calidad", "icon": "⭐"},
                {"title": "Consultoría Especializada", "description": "Asesoría experta adaptada a tus necesidades", "icon": "💼"},
                {"title": "Soporte 24/7", "description": "Atención continua para resolver cualquier duda", "icon": "🛠️"},
                {"title": "Servicio Premium", "description": "Experiencia exclusiva para clientes exigentes", "icon": "🏆"},
                {"title": "Soluciones Personalizadas", "description": "Adaptamos cada servicio a tu caso específico", "icon": "🎯"},
                {"title": "Garantía Total", "description": "Respaldo completo en cada proyecto que realizamos", "icon": "✅"}
            ],
            "about_text": f"Somos una empresa líder en el sector de {industry} con más de 10 años de experiencia brindando soluciones de alta calidad. Nuestro equipo de profesionales está comprometido con la excelencia y la satisfacción total de nuestros clientes. Trabajamos con los más altos estándares de calidad, utilizando las mejores prácticas y tecnologías del mercado para garantizar resultados excepcionales en cada proyecto. Nos enorgullecemos de haber ayudado a cientos de clientes a alcanzar sus objetivos, construyendo relaciones duraderas basadas en la confianza, transparencia y resultados comprobados.",
            "benefits": [
                "Experiencia comprobada",
                "Atención personalizada",
                "Resultados garantizados",
                "Precios competitivos",
                "Soporte continuo",
                "Calidad premium"
            ],
            "stats": [
                {"number": 150, "label": "Clientes Felices", "icon": "😊"},
                {"number": 10, "label": "Años de Experiencia", "icon": "🏆"},
                {"number": 500, "label": "Proyectos Completados", "icon": "✅"},
                {"number": 98, "label": "Satisfacción (%)", "icon": "⭐"}
            ],
            "testimonials": [
                {"name": "María González", "role": "Cliente frecuente", "text": "Excelente servicio, muy profesionales y atentos. Los recomiendo ampliamente a cualquiera que busque calidad.", "rating": 5, "photo_prompt": "mujer profesional latina sonriente retrato corporativo"},
                {"name": "Juan Pérez", "role": "Empresa asociada", "text": "La mejor experiencia que he tenido. Sin duda volveré a contratarlos para futuros proyectos.", "rating": 5, "photo_prompt": "hombre de negocios profesional retrato corporativo"},
                {"name": "Ana Rodríguez", "role": "Cliente nueva", "text": "Me sorprendió la calidad del servicio. Superaron mis expectativas en todos los aspectos.", "rating": 4, "photo_prompt": "profesional mexicana sonriente retrato"}
            ],
            "pricing": [
                {"name": "Básico", "price": "$99", "period": "/mes", "popular": False, "features": ["Servicio básico", "Soporte por email", "1 revisión mensual", "Acceso a recursos"]},
                {"name": "Profesional", "price": "$199", "period": "/mes", "popular": True, "features": ["Todo del Básico", "Soporte prioritario", "Revisiones ilimitadas", "Consultoría mensual"]},
                {"name": "Enterprise", "price": "$399", "period": "/mes", "popular": False, "features": ["Todo del Profesional", "Soporte 24/7", "Consultoría dedicada", "Reportes personalizados"]}
            ],
            "team": [
                {"name": "Carlos Ramírez", "role": "CEO / Fundador", "bio": "Más de 15 años de experiencia liderando proyectos exitosos en la industria."},
                {"name": "Laura Martínez", "role": "Directora de Operaciones", "bio": "Especialista en gestión de proyectos con enfoque en resultados."},
                {"name": "Pedro Sánchez", "role": "Especialista Principal", "bio": "Experto certificado con amplia trayectoria en el sector."},
                {"name": "Sofía López", "role": "Atención al Cliente", "bio": "Dedicada a brindar la mejor experiencia a cada cliente."}
            ],
            "faqs": [
                {"question": f"¿Cuánto tiempo toma el servicio de {industry}?", "answer": "Depende del proyecto, pero generalmente entre 3-5 días hábiles. Para proyectos más complejos, te daremos un cronograma detallado."},
                {"question": "¿Ofrecen garantía en sus servicios?", "answer": "Sí, todos nuestros servicios incluyen garantía de satisfacción. Si no estás conforme, trabajaremos hasta que lo estés."},
                {"question": "¿Cómo puedo pagar?", "answer": "Aceptamos tarjetas de crédito, débito, transferencias bancarias y pagos en efectivo. También ofrecemos planes de pago flexibles."},
                {"question": "¿Hacen entregas a domicilio?", "answer": "Sí, contamos con servicio de entrega en toda la ciudad sin costo adicional para pedidos mayores."},
                {"question": "¿Puedo solicitar una cotización personalizada?", "answer": "Por supuesto. Contáctanos por email o teléfono y te enviaremos una cotización detallada en menos de 24 horas."},
                {"question": "¿Ofrecen atención en fines de semana?", "answer": "Sí, atendemos de lunes a sábado. Para emergencias los domingos, contamos con línea de soporte prioritario."}
            ]
        }