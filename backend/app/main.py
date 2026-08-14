import os, json, logging, time, shutil, collections
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Security, Request
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
# Importar servicios
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.email_service import EmailService
from app.services.website_service import WebsiteService
from app.services.export_service import ExportService
from app.services.auth_service import auth_service
from app.services.payment_service import payment_service, PRICES

logger = logging.getLogger(__name__)

_RATE_BUCKETS = {}

def _check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    bucket = _RATE_BUCKETS.setdefault(key, collections.deque())
    while bucket and bucket[0] < now - window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True

# Rutas de datos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Instanciar servicios
llm_service = LLMService()
rag_service = RAGService()
email_service = EmailService()
website_service = WebsiteService()
export_service = ExportService()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# App FastAPI
app = FastAPI(title="SaaS Platform Pro API", version="1.0.0")

# CORS
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
(DATA_DIR / "websites").mkdir(exist_ok=True)
(DATA_DIR / "exports").mkdir(exist_ok=True)
app.mount("/data/websites", StaticFiles(directory=str(DATA_DIR / "websites")), name="websites")
app.mount("/data/exports", StaticFiles(directory=str(DATA_DIR / "exports")), name="exports")

# ============================================
# MODELOS DE PYDANTIC
# ============================================

class TenantCreateRequest(BaseModel):
    tenant_id: str
    company_name: str
    industry: str
    system_prompt: str = "Asistente"
    main_objective: str = ""
    escalation_email: str = ""

class WebsiteGenerationRequest(BaseModel):
    industry: str
    objective: str
    audience: str
    tone: str
    package: str = "full"
    brand_hex: str = "#2563eb"
    brand_secondary: str = "#764ba2"
    visual_style: str = "moderno"
    page_type: str = "landing"
    calendly_url: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

class ChatRequest(BaseModel):
    question: str
    session_id: str = ""
    email: str = ""

class CheckoutRequest(BaseModel):
    tenant_id: str
    company_name: str
    industry: str
    system_prompt: str = "Asistente"
    main_objective: str = ""
    escalation_email: str = ""
    objective: str = ""
    audience: str = ""
    tone: str = "amigable"
    package: str = "full"
    visual_style: str = "moderno"
    page_type: str = "landing"
    provider: str = "demo"
    calendly_url: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""

# ============================================
# ENDPOINTS DE AUTENTICACIÓN JWT
# ============================================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login con JWT tokens"""
    try:
        users_file = DATA_DIR / "users.json"
        if not users_file.exists():
            raise HTTPException(status_code=500, detail="Archivo de usuarios no encontrado")
        
        with open(users_file, 'r', encoding='utf-8-sig') as f:
            users = json.load(f)
        
        # Buscar usuario
        user = next((u for u in users if u.get("username") == request.username), None)
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar contraseña
        if not auth_service.verify_password(request.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Crear tokens
        access_token = auth_service.create_access_token(
            data={
                "sub": user.get("username"),
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        )
        
        refresh_token = auth_service.create_refresh_token(
            data={
                "sub": user.get("username"),
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        )
        
        logger.info(f"✅ Login exitoso: {request.username}")
        
        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/refresh")
async def refresh_token(request: RefreshRequest):
    """Refrescar access token usando refresh token"""
    try:
        payload = auth_service.decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        
        username = payload.get("username") or payload.get("sub")
        
        # Validar que el usuario siga existiendo
        users_file = DATA_DIR / "users.json"
        users = []
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8-sig') as f:
                users = json.load(f)
        user = next((u for u in users if u.get("username") == username), None)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        user_data = {
            "sub": user.get("username"),
            "username": user.get("username"),
            "role": user.get("role", "user")
        }
        access_token = auth_service.create_access_token(data=user_data)
        refresh_token = auth_service.create_refresh_token(data=user_data)
        
        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user_info(user: dict = Depends(auth_service.get_current_user)):
    """Obtener información del usuario actual"""
    return {
        "status": "success",
        "user": user
    }


@app.post("/api/auth/register")
async def register(request: RegisterRequest, current_user: dict = Depends(auth_service.get_current_user)):
    """Registrar nuevo usuario (solo admins)"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="No autorizado")
        
        users_file = DATA_DIR / "users.json"
        users = []
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8-sig') as f:
                users = json.load(f)
        
        if any(u.get("username") == request.username for u in users):
            raise HTTPException(status_code=400, detail="Usuario ya existe")
        
        new_user = {
            "username": request.username,
            "password_hash": auth_service.hash_password(request.password),
            "role": request.role,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        
        with open(users_file, 'w', encoding='utf-8-sig') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Usuario registrado: {request.username}")
        
        return {
            "status": "success",
            "message": f"Usuario {request.username} creado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ============================================
# ENDPOINTS DE GESTIÓN DE USUARIOS
# ============================================

@app.get("/api/users")
async def list_users(current_user: dict = Depends(auth_service.get_current_user)):
    """Listar todos los usuarios (solo admins)"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Solo admins pueden ver usuarios")
        
        users_file = DATA_DIR / "users.json"
        if not users_file.exists():
            return {"status": "success", "users": []}
        
        with open(users_file, 'r', encoding='utf-8-sig') as f:
            users = json.load(f)
        
        # No exponer password_hash
        safe_users = [
            {
                "username": u.get("username"),
                "role": u.get("role", "user"),
                "created_at": u.get("created_at", "")
            }
            for u in users
        ]
        
        return {"status": "success", "users": safe_users}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users")
async def create_user(request: RegisterRequest, current_user: dict = Depends(auth_service.get_current_user)):
    """Crear nuevo usuario (solo admins)"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Solo admins pueden crear usuarios")
        
        # Validar rol
        if request.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Rol debe ser 'admin' o 'user'")
        
        users_file = DATA_DIR / "users.json"
        users = []
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8-sig') as f:
                users = json.load(f)
        
        # Verificar si ya existe
        if any(u.get("username") == request.username for u in users):
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        
        # Crear usuario
        new_user = {
            "username": request.username,
            "password_hash": auth_service.hash_password(request.password),
            "role": request.role,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        
        with open(users_file, 'w', encoding='utf-8-sig') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Usuario creado: {request.username} (rol: {request.role})")
        
        return {
            "status": "success",
            "message": f"Usuario {request.username} creado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/users/{username}")
async def delete_user(username: str, current_user: dict = Depends(auth_service.get_current_user)):
    """Eliminar usuario (solo admins, no puede eliminarse a sí mismo)"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Solo admins pueden eliminar usuarios")
        
        # No puede eliminarse a sí mismo
        if username == current_user.get("username"):
            raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
        
        users_file = DATA_DIR / "users.json"
        if not users_file.exists():
            raise HTTPException(status_code=404, detail="No hay usuarios")
        
        with open(users_file, 'r', encoding='utf-8-sig') as f:
            users = json.load(f)
        
        # Filtrar usuario a eliminar
        new_users = [u for u in users if u.get("username") != username]
        
        if len(new_users) == len(users):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        with open(users_file, 'w', encoding='utf-8-sig') as f:
            json.dump(new_users, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Usuario eliminado: {username}")
        
        return {"status": "success", "message": f"Usuario {username} eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINT PRINCIPAL (SIRVE EL PANEL ADMIN)
# ============================================

@app.get("/")
async def serve_admin_panel():
    """Sirve el panel admin con headers anti-cache"""
    admin_file = BASE_DIR / "static" / "admin" / "index.html"
    if not admin_file.exists():
        raise HTTPException(status_code=404, detail="Panel no encontrado")
    
    content = admin_file.read_bytes().decode('utf-8')
    
    return HTMLResponse(
        content=content,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
# ============================================
# ENDPOINTS DE HEALTH
# ============================================

@app.get("/health")
async def health():
    return {"status": "ok"}

# ============================================
# ENDPOINTS DE TENANTS (PROTEGIDOS)
# ============================================

def _create_tenant_record(tenant_data: dict) -> dict:
    """Crea un tenant en tenants.json validando el ID. Lanza HTTPException si falla."""
    import re
    tenant_id = (tenant_data.get("tenant_id") or "").strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id es requerido")
    if len(tenant_id) < 3 or len(tenant_id) > 63:
        raise HTTPException(status_code=400, detail="tenant_id debe tener entre 3 y 63 caracteres")
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', tenant_id):
        raise HTTPException(
            status_code=400,
            detail="tenant_id inválido. Solo letras, números, guiones (-) y guiones bajos (_). Sin espacios. Ej: 'dulce-demo'"
        )
    tenants_file = DATA_DIR / "tenants.json"
    tenants = []
    if tenants_file.exists():
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            try:
                tenants = json.load(f)
            except Exception:
                pass
    if any(t.get("tenant_id") == tenant_id or t.get("id") == tenant_id for t in tenants):
        raise HTTPException(status_code=400, detail="El ID del Tenant ya existe")
    new_tenant = dict(tenant_data)
    new_tenant["tenant_id"] = tenant_id
    new_tenant["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    new_tenant["payment_status"] = "pending"
    tenants.append(new_tenant)
    with open(tenants_file, 'w', encoding='utf-8-sig') as f:
        json.dump(tenants, f, indent=2, ensure_ascii=False)
    return new_tenant

@app.post("/api/tenants")
async def create_tenant(request: TenantCreateRequest, current_user: dict = Depends(auth_service.get_current_user)):
    """Crear nuevo tenant (requiere autenticación)"""
    try:
        _create_tenant_record(request.dict())
        return {"status": "success", "message": "Tenant creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tenants")
async def get_tenants(current_user: dict = Depends(auth_service.get_current_user)):
    """Listar todos los tenants (requiere autenticación)"""
    try:
        tenants_file = DATA_DIR / "tenants.json"
        if not tenants_file.exists():
            return {"status": "success", "tenants": []}
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            tenants = json.load(f)
        return {"status": "success", "tenants": tenants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, current_user: dict = Depends(auth_service.get_current_user)):
    """Eliminar tenant (requiere autenticación)"""
    try:
        tenants_file = DATA_DIR / "tenants.json"
        if not tenants_file.exists():
            raise HTTPException(status_code=404, detail="No hay tenants")
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            tenants = json.load(f)
        new_tenants = [t for t in tenants if t.get("tenant_id") != tenant_id and t.get("id") != tenant_id]
        if len(new_tenants) == len(tenants):
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        with open(tenants_file, 'w', encoding='utf-8-sig') as f:
            json.dump(new_tenants, f, indent=2, ensure_ascii=False)
        
        # Eliminar sitio web si existe
        tenant_dir = DATA_DIR / "websites" / tenant_id
        if tenant_dir.exists():
            shutil.rmtree(tenant_dir)
        
        # Eliminar documentos del chatbot
        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id
        if tenant_docs_dir.exists():
            shutil.rmtree(tenant_docs_dir)
        
        return {"status": "success", "message": "Tenant eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE GENERACIÓN DE SITIOS
# ============================================

@app.post("/api/generate/{tenant_id}")
async def generate_service(tenant_id: str, request: WebsiteGenerationRequest, current_user: dict = Depends(auth_service.get_current_user)):
    """Generar sitio web con IA (requiere autenticación)"""
    try:
        result = await website_service.generate_modular_service(
            tenant_id=tenant_id, 
            industry=request.industry, 
            objective=request.objective,
            audience=request.audience, 
            tone=request.tone, 
            package=request.package,
            brand_hex=request.brand_hex,
            brand_secondary=request.brand_secondary,
            visual_style=request.visual_style,
            page_type=request.page_type,
            calendly_url=request.calendly_url,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            contact_address=request.contact_address
        )
        return result
    except Exception as e:
        logger.error(f"Error generando servicio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE DOCUMENTOS / CHATBOT
# ============================================

@app.post("/api/documents/upload/{tenant_id}")
async def upload_document(tenant_id: str, file: UploadFile = File(...), current_user: dict = Depends(auth_service.get_current_user)):
    """Subir documento para el chatbot RAG"""
    try:
        safe_name = os.path.basename(file.filename or "")
        if not safe_name.lower().endswith(('.txt', '.pdf')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt y .pdf")
        
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo excede el limite de 10 MB")
        
        # Guardar el archivo
        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id / "documents"
        tenant_docs_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = tenant_docs_dir / safe_name
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Procesar el documento con RAG
        if safe_name.lower().endswith('.txt'):
            chunks_indexed = await rag_service.process_document(tenant_id, str(file_path))
        else:
            # Para PDF, por ahora solo guardamos
            chunks_indexed = 0
        
        return {
            "status": "success",
            "filename": safe_name,
            "chunks_indexed": chunks_indexed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subiendo documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{tenant_id}")
async def chat_endpoint(tenant_id: str, request: ChatRequest, http_request: Request):
    """Endpoint para el chatbot"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not _check_rate_limit(f"chat:{tenant_id}:{client_ip}", limit=20, window_seconds=60):
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intenta nuevamente en un momento.")
        
        question = request.question
        session_id = request.session_id or "default"
        user_email = request.email
        
        # Obtener respuesta del RAG
        answer = await rag_service.query(tenant_id, question)
        
        # Detectar si el usuario proporcionó un email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        detected_email = re.search(email_pattern, question)
        
        if detected_email:
            user_email = detected_email.group()
        
        # Guardar lead si se detectó email
        if user_email:
            lead_data = {
                "tenant_id": tenant_id,
                "email": user_email,
                "question": question,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Guardar lead
            leads_file = DATA_DIR / "storage" / "leads.json"
            leads_file.parent.mkdir(exist_ok=True)
            leads = []
            if leads_file.exists():
                with open(leads_file, 'r', encoding='utf-8-sig') as f:
                    try: leads = json.load(f)
                    except: pass
            
            # Evitar duplicados
            if not any(l.get("email") == user_email and l.get("tenant_id") == tenant_id for l in leads):
                leads.append(lead_data)
                with open(leads_file, 'w', encoding='utf-8-sig') as f:
                    json.dump(leads, f, indent=2, ensure_ascii=False)
                
                # Enviar notificación por email
                try:
                    tenant_info = next((t for t in json.loads((DATA_DIR / "tenants.json").read_text(encoding="utf-8-sig")) if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
                    company_name = tenant_info.get("company_name", tenant_id) if tenant_info else tenant_id
                    await email_service.send_lead_notification(
                        tenant_id=tenant_id,
                        company_name=company_name,
                        lead_email=user_email,
                        question=question,
                        answer=answer
                    )
                    logger.info(f"✅ Email de lead enviado: {user_email}")
                except Exception as email_error:
                    logger.warning(f"No se pudo enviar email: {email_error}")
        
        return {
            "status": "success",
            "answer": answer["answer"] if isinstance(answer, dict) else answer,
            "is_lead": answer["is_lead"] if isinstance(answer, dict) else False,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return {
            "status": "error",
            "answer": "Lo siento, estoy teniendo problemas técnicos. ¿Podrías intentar de nuevo o dejar tu email para que te contactemos?"
        }


# ============================================
# ENDPOINTS DE DETALLES DE TENANT
# ============================================

@app.get("/api/tenant/{tenant_id}/details")
async def get_tenant_details(tenant_id: str, current_user: dict = Depends(auth_service.get_current_user)):
    """Obtener detalles de un tenant"""
    try:
        tenants_file = DATA_DIR / "tenants.json"
        if not tenants_file.exists():
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            tenants = json.load(f)
        
        tenant = next((t for t in tenants if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        return {
            "status": "success",
            "tenant": tenant
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE EXPORTACIÓN
# ============================================

@app.post("/api/export/{tenant_id}")
async def export_site(tenant_id: str, current_user: dict = Depends(auth_service.get_current_user)):
    """Exportar sitio web como ZIP"""
    try:
        result = export_service.export_site(tenant_id)
        return result
    except Exception as e:
        logger.error(f"Error exportando sitio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE PAGOS
# ============================================

@app.get("/api/payments/config")
async def payments_config():
    """Configuración de pagos: pasarelas disponibles y precios de paquetes"""
    return {
        "status": "success",
        "currency": "USD",
        "providers": payment_service.get_available_providers(),
        "packages": payment_service.get_packages(),
    }


@app.post("/api/payments/checkout")
async def create_payment_checkout(request: CheckoutRequest, current_user: dict = Depends(auth_service.get_current_user)):
    """Crear tenant + orden + redirección al checkout de la pasarela"""
    try:
        provider = request.provider
        valid_providers = [p["id"] for p in payment_service.get_available_providers()]
        if provider not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Metodo de pago no disponible. Opciones: {', '.join(valid_providers)}")

        tenant_data = {
            "tenant_id": request.tenant_id,
            "company_name": request.company_name,
            "industry": request.industry,
            "system_prompt": request.system_prompt,
            "main_objective": request.main_objective,
            "escalation_email": request.escalation_email,
        }
        _create_tenant_record(tenant_data)

        site_config = {
            "industry": request.industry,
            "objective": request.objective,
            "audience": request.audience,
            "tone": request.tone,
            "brand_hex": "#2563eb",
            "brand_secondary": "#764ba2",
            "visual_style": request.visual_style,
            "page_type": request.page_type,
            "calendly_url": request.calendly_url,
            "contact_email": request.contact_email,
            "contact_phone": request.contact_phone,
            "contact_address": request.contact_address,
        }
        order = payment_service.create_order(request.tenant_id, request.package, provider, site_config)
        checkout_url = await payment_service.create_checkout(order)
        return {
            "status": "success",
            "order_id": order["order_id"],
            "checkout_url": checkout_url,
            "amount": order["amount"],
            "currency": order["currency"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/payments/status/{order_id}")
async def get_payment_status(order_id: str, http_request: Request):
    """Consulta el estado de una orden (publico para el checkout, con rate limit)"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _check_rate_limit(f"paystatus:{order_id}:{client_ip}", limit=60, window_seconds=60):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes.")
    try:
        return await payment_service.get_order_status(order_id)
    except Exception as e:
        logger.error(f"Error consultando estado de pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payments/finalize/{order_id}")
async def finalize_payment(order_id: str, http_request: Request):
    """Genera la entrega cuando la orden esta pagada (publico para el checkout, idempotente)"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _check_rate_limit(f"payfinalize:{order_id}:{client_ip}", limit=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes.")
    try:
        return await payment_service.finalize(order_id)
    except Exception as e:
        logger.error(f"Error finalizando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/checkout-return", response_class=HTMLResponse)
async def checkout_return_page(request: Request):
    """Pagina que confirma el pago y dispara la generacion"""
    return templates.TemplateResponse("checkout_return.html", {"request": request, "message": "Verificando pago"})


@app.get("/checkout-cancel", response_class=HTMLResponse)
async def checkout_cancel_page(request: Request):
    """Pagina de pago cancelado"""
    return templates.TemplateResponse("checkout_cancel.html", {"request": request, "message": "Pago cancelado"})


# ============================================
# ENDPOINTS DE ANALYTICS
# ============================================

@app.get("/api/analytics/global")
async def get_global_analytics(current_user: dict = Depends(auth_service.get_current_user)):
    """Obtener métricas globales con datos para gráficas"""
    try:
        # Leer tenants
        tenants_file = DATA_DIR / "tenants.json"
        tenants = []
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                tenants = json.load(f)
        
        # Leer conversaciones
        conversations_file = DATA_DIR / "storage" / "conversations.json"
        conversations = []
        if conversations_file.exists():
            with open(conversations_file, 'r', encoding='utf-8-sig') as f:
                try:
                    conversations = json.load(f)
                except:
                    conversations = []
        
        # Leer leads
        leads_file = DATA_DIR / "storage" / "leads.json"
        leads = []
        if leads_file.exists():
            with open(leads_file, 'r', encoding='utf-8-sig') as f:
                try:
                    leads = json.load(f)
                except:
                    leads = []
        
        # === MÉTRICAS BÁSICAS ===
        total_tenants = len(tenants)
        total_conversations = len(conversations)
        total_leads = len(leads)
        
        # === GRÁFICA 1: Empresas por industria ===
        industries_count = {}
        for t in tenants:
            ind = t.get("industry", "Sin especificar")
            industries_count[ind] = industries_count.get(ind, 0) + 1
        
        # === GRÁFICA 2: Distribución de paquetes ===
        packages_count = {"full": 0, "web_chat": 0, "chat_only": 0, "seo_only": 0}
        for t in tenants:
            pkg = t.get("package", "sin_paquete")
            if pkg in packages_count:
                packages_count[pkg] += 1
            else:
                packages_count.setdefault(pkg, 1)
        packages_count = {k: v for k, v in packages_count.items() if v > 0}

        # === INGRESOS ESTIMADOS (precios de paquetes) ===
        package_prices = PRICES
        total_revenue = sum(
            count * package_prices.get(pkg, 0) for pkg, count in packages_count.items()
        )
        
        # === GRÁFICA 3: Leads por día (últimos 7 días) ===
        from datetime import datetime, timedelta
        leads_by_day = {}
        today = datetime.now()
        for i in range(7):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            leads_by_day[day] = 0
        
        for lead in leads:
            lead_date = lead.get("timestamp", "")
            if lead_date:
                try:
                    day = lead_date.split("T")[0]
                    if day in leads_by_day:
                        leads_by_day[day] += 1
                except:
                    pass
        
        # Ordenar por fecha
        leads_timeline = [
            {"date": k, "count": v} 
            for k, v in sorted(leads_by_day.items())
        ]
        
        # === TOP 5 EMPRESAS POR CONVERSACIONES ===
        tenant_conversations = {}
        for conv in conversations:
            tid = conv.get("tenant_id", "")
            if tid:
                tenant_conversations[tid] = tenant_conversations.get(tid, 0) + 1
        
        top_tenants = sorted(
            tenant_conversations.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Obtener nombres de las empresas top
        top_companies = []
        for tid, count in top_tenants:
            tenant = next((t for t in tenants if (t.get("tenant_id") or t.get("id")) == tid), None)
            name = tenant.get("company_name", tid) if tenant else tid
            top_companies.append({"name": name, "conversations": count})
        
        return {
            "status": "success",
            "metrics": {
                "total_tenants": total_tenants,
                "total_conversations": total_conversations,
                "total_leads": total_leads,
                "monthly_revenue_estimate": total_revenue
            },
            "charts": {
                "industries": industries_count,
                "packages": packages_count,
                "leads_timeline": leads_timeline,
                "top_companies": top_companies
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ============================================
# ENDPOINTS DE EDICION VISUAL
# ============================================

@app.get("/api/site-editor/{tenant_id}")
async def get_site_editor_data(tenant_id: str, current_user: dict = Depends(auth_service.get_current_user)):
    """Obtener datos editables del sitio"""
    try:
        site_data_file = DATA_DIR / "websites" / tenant_id / "site_data.json"
        if not site_data_file.exists():
            raise HTTPException(status_code=404, detail="Sitio no encontrado")
        
        with open(site_data_file, 'r', encoding='utf-8-sig') as f:
            site_data = json.load(f)
        
        # Extraer solo campos editables
        editable = {
            "company_name": site_data.get("company_name", ""),
            "hero_title": site_data.get("hero_title", ""),
            "hero_subtitle": site_data.get("hero_subtitle", ""),
            "hero_cta": site_data.get("hero_cta", ""),
            "hero_image": site_data.get("hero_image", ""),
            "about_title": site_data.get("about_title", ""),
            "about_text": site_data.get("about_text", ""),
            "about_image": site_data.get("about_image", ""),
            "contact_email": site_data.get("contact_email", ""),
            "contact_phone": site_data.get("contact_phone", ""),
            "contact_address": site_data.get("contact_address", ""),
            "brand_hex": site_data.get("brand_hex", "#2563eb"),
            "brand_secondary": site_data.get("brand_secondary", "#764ba2"),
            "visual_style": site_data.get("visual_style", "moderno"),
            "services": site_data.get("services", []),
            "gallery_images": site_data.get("gallery_images", [])
        }
        
        return {"status": "success", "data": editable}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo datos de edicion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/site-editor/{tenant_id}")
async def save_site_editor_data(tenant_id: str, data: dict, current_user: dict = Depends(auth_service.get_current_user)):
    """Guardar cambios del editor y regenerar sitio"""
    try:
        site_data_file = DATA_DIR / "websites" / tenant_id / "site_data.json"
        if not site_data_file.exists():
            raise HTTPException(status_code=404, detail="Sitio no encontrado")
        
        # Leer datos actuales
        with open(site_data_file, 'r', encoding='utf-8-sig') as f:
            site_data = json.load(f)
        
        # Actualizar campos editables
        for key in data:
            if key in site_data:
                site_data[key] = data[key]
        
        # Guardar cambios
        with open(site_data_file, 'w', encoding='utf-8-sig') as f:
            json.dump(site_data, f, indent=2, ensure_ascii=False)
        
        # Regenerar el sitio HTML
        website_service.regenerate_site(tenant_id, site_data)
        
        logger.info(f"Sitio {tenant_id} actualizado via editor")
        
        return {
            "status": "success",
            "message": "Cambios guardados y sitio regenerado",
            "preview_url": f"/data/websites/{tenant_id}/index.html"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error guardando cambios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)