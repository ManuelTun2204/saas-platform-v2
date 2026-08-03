import os
import logging
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = "https://openrouter.ai/api/v1"

    def get_llm(self, temperature: float = 0.2, max_tokens: int = 400):
        """
        Obtiene una instancia del LLM optimizada para velocidad y precisión.
        - temperature=0.2: Respuestas más deterministas, directas y menos alucinadas.
        - max_tokens=400: Respuestas concisas que se generan mucho más rápido.
        - model: Prioriza modelos de 8B que son extremadamente rápidos y baratos.
        """
        if not self.api_key or not self.api_key.startswith("sk-or-"):
            logger.warning("⚠️ OPENROUTER_API_KEY no configurada o inválida.")
            raise ValueError("OpenRouter API Key no configurada.")

        return ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            model="meta-llama/llama-3-8b-instruct", # Modelo rápido y eficiente
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30 # Timeout para evitar bloqueos infinitos
        )

    def get_fallback_llm(self, temperature: float = 0.2, max_tokens: int = 400):
        """
        Modelo de respaldo gratuito en caso de que el principal falle o esté saturado.
        """
        return ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            model="mistralai/mistral-7b-instruct:free",
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30
        )