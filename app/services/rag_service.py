import os
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import pypdf

from app.services.llm_service import LLMService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# Ruta base para bases vectoriales: /app/data/tenants
TENANTS_DIR = Path(__file__).parent.parent.parent / "data" / "tenants"
TENANTS_DIR.mkdir(parents=True, exist_ok=True)

class RAGService:
    """Servicio RAG con ChromaDB y memoria de conversación"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.storage = StorageService()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if self.openrouter_key:
            self.embedding_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_key
            )
        else:
            self.embedding_client = None
            logger.warning("⚠️ OPENROUTER_API_KEY no configurada. Embeddings deshabilitados.")
    
    def _get_chroma_client(self, tenant_id: str) -> chromadb.Client:
        """Obtiene cliente ChromaDB persistente por tenant"""
        tenant_dir = TENANTS_DIR / tenant_id / "vector_db"
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        return chromadb.PersistentClient(path=str(tenant_dir))
    
    def _get_embedding(self, text: str) -> List[float]:
        """Genera embedding usando OpenRouter (modelo gratuito)"""
        if not self.embedding_client:
            raise Exception("Embedding client no configurado")
        
        try:
            response = self.embedding_client.embeddings.create(
                model="openai/text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Divide texto en chunks con overlap"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += chunk_size - overlap
        return chunks
    
    async def process_document(self, tenant_id: str, file_path: Path) -> int:
        """Procesa un documento (PDF/TXT) y lo indexa en ChromaDB"""
        logger.info(f"Procesando documento: {file_path.name} para tenant {tenant_id}")
        
        # 1. Extraer texto
        if file_path.suffix.lower() == ".pdf":
            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                text = "\n".join([page.extract_text() for page in pdf.pages])
        else:  # TXT
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        if not text.strip():
            logger.warning(f"Documento vacío: {file_path.name}")
            return 0
        
        # 2. Chunking
        chunks = self._chunk_text(text)
        logger.info(f"Generados {len(chunks)} chunks")
        
        # 3. Generar embeddings e indexar
        chroma_client = self._get_chroma_client(tenant_id)
        collection = chroma_client.get_or_create_collection(name=f"docs_{tenant_id}")
        
        ids = []
        embeddings = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            try:
                embedding = self._get_embedding(chunk)
                ids.append(f"{file_path.stem}_{i}")
                embeddings.append(embedding)
                documents.append(chunk)
            except Exception as e:
                logger.error(f"Error procesando chunk {i}: {e}")
                continue
        
        if ids:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents
            )
            logger.info(f"✅ Indexados {len(ids)} chunks en ChromaDB")
        
        return len(ids)
    
    async def query(self, tenant_id: str, question: str, session_id: str) -> Dict:
        """Responde una pregunta usando RAG + memoria"""
        logger.info(f"Query RAG para tenant {tenant_id}, session {session_id}")
        
        # 1. Obtener contexto relevante de ChromaDB
        chroma_client = self._get_chroma_client(tenant_id)
        
        try:
            collection = chroma_client.get_collection(name=f"docs_{tenant_id}")
        except:
            return {
                "answer": "No tengo información sobre este tema. Por favor, contacta directamente al negocio.",
                "sources": [],
                "is_lead": False
            }
        
        # 2. Buscar documentos relevantes
        try:
            question_embedding = self._get_embedding(question)
            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=3
            )
            
            context = "\n\n".join(results['documents'][0]) if results['documents'] else ""
            sources = list(set([doc.split('_')[0] for doc in results['ids'][0]])) if results['ids'] else []
        except Exception as e:
            logger.error(f"Error en búsqueda vectorial: {e}")
            context = ""
            sources = []
        
        # 3. Obtener historial de conversación (memoria)
        conversations = self.storage.get_conversations_by_tenant(tenant_id)
        session_convs = [c for c in conversations if c.get("session_id") == session_id]
        
        # Mantener últimas 10 interacciones
        memory = session_convs[-10:] if len(session_convs) > 10 else session_convs
        memory_text = "\n".join([f"{c['role']}: {c['content']}" for c in memory])
        
        # 4. Generar respuesta con contexto + memoria
        prompt = f"""Eres un asistente virtual amigable y profesional. Responde basándote ÚNICAMENTE en el contexto proporcionado.

Contexto del negocio:
{context}

Historial de conversación:
{memory_text}

Pregunta del usuario: {question}

Instrucciones:
- Responde de forma concisa y útil
- Si no encuentras la respuesta en el contexto, di amablemente que no tienes esa información
- No inventes información
- Si el usuario pregunta por precios o disponibilidad, sugiere que deje su email para contacto"""

        answer = await self.llm_service.generate_content(prompt, max_tokens=500, temperature=0.7)
        
        # 5. Detectar si es un lead (email en la pregunta)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        is_lead = bool(re.search(email_pattern, question))
        
        if is_lead:
            email_match = re.search(email_pattern, question)
            if email_match:
                lead_data = {
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "email": email_match.group(),
                    "question": question,
                    "timestamp": str(Path().cwd())
                }
                self.storage.save_lead(lead_data)
                logger.info(f"🎯 Lead capturado: {lead_data['email']}")
        
        # 6. Guardar conversación
        self.storage.save_conversation({
            "tenant_id": tenant_id,
            "session_id": session_id,
            "role": "user",
            "content": question,
            "timestamp": str(Path().cwd())
        })
        self.storage.save_conversation({
            "tenant_id": tenant_id,
            "session_id": session_id,
            "role": "assistant",
            "content": answer,
            "timestamp": str(Path().cwd())
        })
        
        return {
            "answer": answer,
            "sources": sources,
            "is_lead": is_lead
        }
