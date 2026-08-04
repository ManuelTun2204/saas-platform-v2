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
        """Genera JSON estructurado para sitio web"""
        prompt = f"""Eres un experto diseñador web y copywriter. Genera contenido para un sitio web profesional.

INDUSTRIA: {industry}
OBJETIVO: {objective}
AUDIENCIA: {audience}
TONO: {tone}
ESTILO VISUAL: {visual_style}

Devuelve SOLO un objeto JSON válido (sin markdown, sin ```json) con esta estructura EXACTA:
{{
    "company_name": "Nombre creativo de la empresa",
    "hero_title": "Título principal impactante (máx 60 chars)",
    "hero_subtitle": "Subtítulo descriptivo (máx 120 chars)",
    "hero_cta": "Texto del botón principal (Ej: 'Cotiza ahora')",
    "services": [
        {{"title": "Servicio 1", "description": "Descripción breve", "icon": "emoji"}},
        {{"title": "Servicio 2", "description": "Descripción breve", "icon": "emoji"}},
        {{"title": "Servicio 3", "description": "Descripción breve", "icon": "emoji"}}
    ],
    "about_text": "Párrafo sobre la empresa (100-150 palabras)",
    "benefits": ["Beneficio 1", "Beneficio 2", "Beneficio 3", "Beneficio 4"],
    "testimonials": [
        {{"name": "Cliente 1", "role": "Cargo", "text": "Testimonio breve"}},
        {{"name": "Cliente 2", "role": "Cargo", "text": "Testimonio breve"}}
    ],
    "faqs": [
        {{"question": "¿Pregunta frecuente 1?", "answer": "Respuesta clara"}},
        {{"question": "¿Pregunta frecuente 2?", "answer": "Respuesta clara"}},
        {{"question": "¿Pregunta frecuente 3?", "answer": "Respuesta clara"}}
    ]
}}

IMPORTANTE: Devuelve SOLO el JSON, sin texto adicional, sin markdown."""

        try:
            raw_response = await self.generate_content(prompt, max_tokens=2000, temperature=0.7)
            
            # Limpiar markdown si viene
            cleaned = raw_response.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            cleaned = cleaned.strip()
            
            # Intentar parsear
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Intentar extraer JSON del texto
                match = re.search(r'\{[\s\S]*\}', cleaned)
                if match:
                    return json.loads(match.group())
                raise
                
        except Exception as e:
            logger.error(f"Error parseando JSON: {e}")
            # Fallback por defecto
            return {
                "company_name": f"{industry.title()} Pro",
                "hero_title": f"Soluciones profesionales en {industry}",
                "hero_subtitle": objective,
                "hero_cta": "Contáctanos",
                "services": [
                    {"title": "Servicio Principal", "description": "Servicio profesional", "icon": "⭐"},
                    {"title": "Consultoría", "description": "Asesoría experta", "icon": "💼"},
                    {"title": "Soporte", "description": "Atención 24/7", "icon": "🛠️"}
                ],
                "about_text": f"Somos expertos en {industry}. {objective}.",
                "benefits": ["Experiencia comprobada", "Atención personalizada", "Resultados garantizados", "Precios competitivos"],
                "testimonials": [
                    {"name": "Cliente Satisfecho", "role": "Empresa", "text": "Excelente servicio"}
                ],
                "faqs": [
                    {"question": "¿Cómo los contacto?", "answer": "Por email o teléfono"}
                ]
            }