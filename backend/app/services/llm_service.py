import os
import json
import logging
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key or not self.api_key.startswith("sk-or-"):
            logger.warning("⚠️ OPENROUTER_API_KEY no configurada o inválida.")

    def _get_llm(self, temperature: float = 0.7, max_tokens: int = 2000):
        """LLM principal con fallback automático"""
        try:
            return ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model="meta-llama/llama-3.1-8b-instruct",
                temperature=temperature,
                max_tokens=max_tokens,
                request_timeout=60
            )
        except Exception as e:
            logger.warning(f"Fallo LLM principal: {e}. Usando fallback...")
            return ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model="mistralai/mistral-7b-instruct:free",
                temperature=temperature,
                max_tokens=max_tokens,
                request_timeout=60
            )

    async def generate_content(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.7) -> str:
        """Genera texto libre basado en un prompt"""
        try:
            llm = self._get_llm(temperature=temperature, max_tokens=max_tokens)
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error en generate_content: {e}")
            raise Exception(f"Error generando contenido: {str(e)}")

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
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones elogiando el servicio", "rating": 5}},
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones sobre la experiencia", "rating": 5}},
        {{"name": "Nombre realista hispano", "role": "Cargo o relación con la empresa", "text": "Testimonio auténtico de 2-3 oraciones recomendando el servicio", "rating": 4}}
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
    ]
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
            raw_response = await self.generate_content(prompt, max_tokens=3000, temperature=0.7)
            
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
                {"name": "María González", "role": "Cliente frecuente", "text": "Excelente servicio, muy profesionales y atentos. Los recomiendo ampliamente a cualquiera que busque calidad.", "rating": 5},
                {"name": "Juan Pérez", "role": "Empresa asociada", "text": "La mejor experiencia que he tenido. Sin duda volveré a contratarlos para futuros proyectos.", "rating": 5},
                {"name": "Ana Rodríguez", "role": "Cliente nueva", "text": "Me sorprendió la calidad del servicio. Superaron mis expectativas en todos los aspectos.", "rating": 4}
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