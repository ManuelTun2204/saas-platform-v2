import os
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

# Imports de LangChain (ajusta las rutas de importación si tu proyecto las tiene diferente)
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, tenant_config):
        self.tenant = tenant_config
        # Ajusta DATA_DIR según tu configuración (ej: os.getenv("DATA_DIR", "./data"))
        self.tenant_dir = Path(os.getenv("DATA_DIR", "./data")) / tenant_config.tenant_id
        self.vector_db_path = self.tenant_dir / "vector_db"
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        )
        
        self.vectorstore = Chroma(
            persist_directory=str(self.vector_db_path),
            embedding_function=self.embeddings
        )
    
    def load_documents(self, file_paths: List[str]):
        """Carga documentos desde archivos"""
        documents = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue
            
            if path.suffix == '.pdf':
                loader = PyPDFLoader(str(path))
            elif path.suffix == '.txt':
                loader = TextLoader(str(path), encoding='utf-8')
            elif path.suffix == '.csv':
                loader = CSVLoader(str(path), encoding='utf-8')
            else:
                continue
            
            documents.extend(loader.load())
        return documents
    
    def process_and_store(self, documents):
        """Procesa documentos en chunks y los almacena"""
        # OPTIMIZACIÓN: Chunk size 600 y overlap 80 para no cortar oraciones y mantener contexto
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", 600)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 80)),
            length_function=len,
        )
        
        chunks = text_splitter.split_documents(documents)
        
        if len(chunks) > 0:
            self.vectorstore.add_documents(chunks)
            self.vectorstore.persist()
        
        return len(chunks)
    
    def create_qa_chain(self, llm, chat_history: Optional[List] = None):
        """Crea cadena de conversación con memoria optimizada para velocidad y precisión"""
        
        # System prompt OPTIMIZADO: Estricto, directo y a prueba de alucinaciones
        system_prompt = f"""Eres el asistente virtual oficial de {self.tenant.company_name}. 
Tu objetivo es ser útil, preciso y extremadamente conciso.

REGLAS ESTRICTAS DE COMPORTAMIENTO:
1. Responde ÚNICAMENTE basándote en el "CONTEXTO DE LA EMPRESA" proporcionado abajo. No inventes información.
2. Sé directo y conciso. Evita introducciones largas o relleno. Ve al grano (máximo 3-4 oraciones).
3. Si el usuario hace una pregunta compleja o larga, identifica la intención principal y responde a esa necesidad específica.
4. Si la respuesta NO está en el contexto, responde exactamente: "No cuento con esa información específica en este momento. ¿Te gustaría que un especialista te contacte para resolverlo?"
5. Mantén un tono profesional, amable y orientado a la solución.
6. Si el usuario muestra interés en contratar, pide precios o deja un correo, confirma el interés y sugiere agendar una cita o dejar sus datos de contacto.
"""
        
        # Prompt para QA conversacional optimizado
        question_prompt = PromptTemplate(
            template=f"""{system_prompt}

CONTEXTO DE LA EMPRESA (USA SOLO ESTA INFORMACIÓN):
{{context}}

HISTORIAL DE CONVERSACIÓN RECIENTE:
{{chat_history}}

PREGUNTA DEL CLIENTE: {{question}}

RESPUESTA CONCISA Y PROFESIONAL:""",
            input_variables=["context", "chat_history", "question"]
        )
        
        # Retriever optimizado: k=3 es más rápido y suele ser más preciso que k=4 o 5
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Memoria de conversación
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="question",
            output_key="answer",
            return_messages=True
        )
        
        # Agregar historial si existe (limitado a 6 para no saturar el contexto y ganar velocidad)
        if chat_history:
            recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
            for human_msg, ai_msg in recent_history:
                memory.save_context(
                    {"question": human_msg},
                    {"answer": ai_msg}
                )
        
        # Cadena conversacional
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": question_prompt},
            verbose=False # Mantener en False para producción (ahorra logs y tiempo)
        )
        
        return qa_chain