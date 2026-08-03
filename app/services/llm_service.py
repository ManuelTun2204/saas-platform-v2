import os, logging, json
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if openrouter_key and openrouter_key.startswith("sk-or-"):
            self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)
        else:
            self.client = None

    async def generate_content(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        if not self.client: raise Exception("OpenRouter no configurado.")
        models = ["meta-llama/llama-3.3-70b-instruct", "meta-llama/llama-3.1-8b-instruct:free"]
        for model in models:
            try:
                completion = self.client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=temperature)
                return completion.choices[0].message.content.strip()
            except Exception: continue
        raise Exception("Modelos fallaron.")

    async def generate_website_json(self, industry: str, objective: str, audience: str, tone: str, visual_style: str) -> dict:
        prompt = f"""
        Eres un experto en diseño web premium. Genera SOLO un objeto JSON válido (sin markdown) para un sitio web de estilo '{visual_style}':
        - Industria: {industry}
        - Objetivo: {objective}
        - Audiencia: {audience}
        - Tono: {tone}
        
        Estructura exacta requerida:
        {{
            "template_type": "landing",
            "google_font": "Inter",
            "hero_image_keyword": "A highly specific, award-winning photography prompt in English for the main hero background. Style: {visual_style}. Subject related to {industry}. 8k, photorealistic, cinematic lighting.",
            "secondary_image_keyword": "A specific photography prompt for a secondary section (e.g., team, workspace, or product detail). Style: {visual_style}. 8k, photorealistic.",
            "service_images": [
                "Specific photography prompt for service 1 related to {industry}. 8k, photorealistic.",
                "Specific photography prompt for service 2 related to {industry}. 8k, photorealistic.",
                "Specific photography prompt for service 3 related to {industry}. 8k, photorealistic."
            ],
            "hero_title": "Título principal impactante (máximo 8 palabras)",
            "hero_subtitle": "Subtítulo persuasivo (máximo 15 palabras)",
            "services": [
                {{"title": "Servicio Premium 1", "description": "Descripción orientada a beneficios (máx 25 palabras)"}},
                {{"title": "Servicio Premium 2", "description": "Descripción orientada a beneficios (máx 25 palabras)"}},
                {{"title": "Servicio Premium 3", "description": "Descripción orientada a beneficios (máx 25 palabras)"}}
            ],
            "cta_text": "Agendar Cita Gratuita"
        }}
        """
        response = await self.generate_content(prompt, max_tokens=1500, temperature=0.6)
        response = response.replace("```json", "").replace("```", "").strip()
        try: return json.loads(response)
        except json.JSONDecodeError: raise ValueError("JSON inválido.")
