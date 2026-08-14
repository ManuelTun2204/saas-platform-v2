import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.storage_service import StorageService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

class RAGService:
    def __init__(self):
        """Constructor global SIN parámetros - maneja múltiples tenants dinámicamente"""
        self.storage = StorageService()
        self.llm_service = LLMService()
        
        # Inicializar embeddings una sola vez (es costoso)
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("✅ Embeddings inicializados correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando embeddings: {e}")
            self.embeddings = None
        
        # Cache de vectorstores por tenant
        self._vectorstore_cache = {}

    def _get_tenant_vectorstore(self, tenant_id: str):
        """Obtiene o crea el vectorstore para un tenant específico"""
        if tenant_id in self._vectorstore_cache:
            return self._vectorstore_cache[tenant_id]
        
        if not self.embeddings:
            raise Exception("Embeddings no inicializados")
        
        tenant_dir = DATA_DIR / "tenants" / tenant_id
        vector_db_path = tenant_dir / "vector_db"
        vector_db_path.mkdir(parents=True, exist_ok=True)
        
        try:
            vectorstore = Chroma(
                persist_directory=str(vector_db_path),
                embedding_function=self.embeddings,
                collection_name=f"tenant_{tenant_id}"
            )
            self._vectorstore_cache[tenant_id] = vectorstore
            return vectorstore
        except Exception as e:
            logger.error(f"Error creando vectorstore para {tenant_id}: {e}")
            raise

    async def process_document(self, tenant_id: str, file_path) -> int:
        """Procesa un documento y lo indexa en la DB vectorial del tenant"""
        path = Path(file_path)
        if not path.exists():
            raise Exception(f"Archivo no encontrado: {path}")
        
        # Cargar documento según extensión
        if path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(path))
        elif path.suffix.lower() == '.txt':
            loader = TextLoader(str(path), encoding='utf-8')
        elif path.suffix.lower() == '.csv':
            loader = CSVLoader(str(path), encoding='utf-8')
        else:
            raise Exception(f"Extensión no soportada: {path.suffix}")
        
        documents = loader.load()
        
        # Dividir en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Indexar en vectorstore del tenant
        vectorstore = self._get_tenant_vectorstore(tenant_id)
        if chunks:
            vectorstore.add_documents(chunks)
            vectorstore.persist()
            logger.info(f"✅ Indexados {len(chunks)} chunks para tenant {tenant_id}")
        
        return len(chunks)

    async def query(self, tenant_id: str, question: str, session_id: str = "default") -> dict:
        """Responde preguntas usando RAG + memoria de conversación"""
        try:
            vectorstore = self._get_tenant_vectorstore(tenant_id)
            
            # Buscar información relevante
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # Obtener contexto
            docs = await retriever.ainvoke(question)
            context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No hay contexto disponible"
            
            # Obtener tenant info
            tenant_info = self.storage.get_tenant(tenant_id)
            company_name = tenant_info.get("company_name", "la empresa") if tenant_info else "la empresa"
            system_prompt = tenant_info.get("system_prompt", f"Eres el asistente virtual de {company_name}") if tenant_info else f"Eres el asistente virtual de {company_name}"
            
            # Obtener historial de conversación
            conversations = self.storage.get_conversations_by_tenant(tenant_id)
            recent_convs = [c for c in conversations if c.get("session_id") == session_id][-6:]
            
            # Construir historial para el prompt
            history_text = ""
            if recent_convs:
                history_text = "\n".join([
                    f"Cliente: {c.get('question', '')}\nAsistente: {c.get('answer', '')}"
                    for c in recent_convs
                ])
            
            # Prompt final
            full_prompt = f"""{system_prompt}

REGLAS:
1. Responde ÚNICAMENTE basándote en el CONTEXTO proporcionado.
2. Sé conciso (máximo 3-4 oraciones).
3. Si no sabes la respuesta, di: "No cuento con esa información. ¿Te gustaría que un especialista te contacte?"
4. Si el usuario muestra interés o da su email, sugiere agendar una cita.

CONTEXTO DE LA EMPRESA:
{context}

{f'HISTORIAL RECIENTE:{chr(10)}{history_text}' if history_text else ''}

PREGUNTA DEL CLIENTE: {question}

RESPUESTA:"""
            
            # Generar respuesta con LLM
            answer = await self.llm_service.generate_content(full_prompt, max_tokens=400, temperature=0.3)
            
                        # Detectar si es un lead (contiene email)
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails_found = re.findall(email_pattern, question)
            is_lead = len(emails_found) > 0 or any(word in question.lower() for word in ['contratar', 'precio', 'costo', 'cotizar', 'comprar'])
            
            # Guardar lead si aplica (solo si hay email)
            if is_lead and emails_found:
                lead_data = {
                    "tenant_id": tenant_id,
                    "email": emails_found[0],
                    "session_id": session_id,
                    "captured_at": datetime.now().isoformat(),
                    "source": "chatbot"
                }
                self.storage.save_lead(lead_data)
                
                # ✅ ENVIAR NOTIFICACIÓN POR EMAIL (DENTRO del if con try/except)
                try:
                    from app.services.email_service import EmailService
                    email_service = EmailService()
                    tenant_info = self.storage.get_tenant(tenant_id)
                    company_name = tenant_info.get("company_name", tenant_id) if tenant_info else tenant_id
                    await email_service.send_lead_notification(
                        tenant_id=tenant_id,
                        company_name=company_name,
                        lead_email=emails_found[0],
                        question=question,
                        answer=answer
                    )
                except Exception as email_error:
                    logger.error(f"⚠️ Error enviando email de lead (no crítico): {email_error}")
            
            # Guardar conversación (siempre)
            conv_data = {
                "tenant_id": tenant_id,
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "is_lead": is_lead,
                "timestamp": datetime.now().isoformat()
            }
            self.storage.save_conversation(conv_data)
            
            return {"answer": answer, "is_lead": is_lead}
            
        except Exception as e:
            logger.error(f"Error en query RAG: {e}", exc_info=True)
            return {
                "answer": "Lo siento, estoy teniendo problemas técnicos. ¿Podrías intentar de nuevo o dejar tu email para que te contactemos?",
                "is_lead": False
            }