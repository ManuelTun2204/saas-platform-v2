from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json, logging, time, secrets
from datetime import datetime
from passlib.context import CryptContext
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from app.services.website_service import WebsiteService
from app.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SaaS Platform V2", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# --- Modelos ---
class WebsiteGenerationRequest(BaseModel):
    industry: str
    objective: str
    audience: str
    tone: str
    package: str = "full"
    brand_hex: str = "#2563eb"  # Color principal de la marca (default: azul)
    visual_style: str = "modern" # modern, elegant, bold, minimalist
    calendly_url: str = ""       # Link de Calendly o sistema de reservas
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""

class TenantCreateRequest(BaseModel):
    tenant_id: str
    company_name: str
    industry: str
    system_prompt: str
    main_objective: str
    escalation_email: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"

class LoginRequest(BaseModel):
    username: str
    password: str

# --- Configuración de Autenticación (pbkdf2_sha256 no tiene límite de 72 bytes) ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
USERS_FILE = DATA_DIR / "users.json"

def get_users():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8-sig') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# --- Servicios ---
website_service = WebsiteService()
rag_service = RAGService()

# --- Endpoints ---
@app.get("/")
async def serve_frontend():
    return FileResponse(str(STATIC_DIR / "admin" / "index.html"))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/auth/register")
async def register_user(user: UserCreate):
    try:
        if len(user.password) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        if len(user.password) > 128:
            raise HTTPException(status_code=400, detail="La contraseña no puede tener más de 128 caracteres")
            
        users = get_users()
        if any(u["username"] == user.username for u in users):
            raise HTTPException(status_code=400, detail="Usuario ya existe")
        
        new_user = {
            "id": str(len(users) + 1),
            "username": user.username,
            "hashed_password": pwd_context.hash(user.password),
            "role": user.role,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        save_users(users)
        
        token = secrets.token_urlsafe(32)
        return {"status": "success", "message": "Usuario creado", "token": token, "user": {"username": user.username, "role": user.role}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        users = get_users()
        user = next((u for u in users if u["username"] == request.username), None)
        if not user or not pwd_context.verify(request.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = secrets.token_urlsafe(32)
        return {"status": "success", "token": token, "user": {"username": user["username"], "role": user["role"]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import re

@app.post("/api/tenants")
async def create_tenant(tenant: dict):
    tenant_id = tenant.get("tenant_id", "").strip()
    
    # VALIDACIÓN: tenant_id debe ser válido para ChromaDB
    if not tenant_id:
        return {"status": "error", "detail": "tenant_id es requerido"}
    
    if len(tenant_id) < 3 or len(tenant_id) > 63:
        return {"status": "error", "detail": "tenant_id debe tener entre 3 y 63 caracteres"}
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', tenant_id):
        return {
            "status": "error", 
            "detail": "tenant_id inválido. Solo usa letras, números, guiones (-) y guiones bajos (_). Sin espacios. Ejemplo: 'dulce-tentacion' o 'pasteleria_vip'"
        }
    
    # ... resto del código existente
async def create_tenant(request: TenantCreateRequest):
    try:
        tenants_file = DATA_DIR / "tenants.json"
        tenants = []
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                try: tenants = json.load(f)
                except: pass
        
        if any(t.get("tenant_id") == request.tenant_id or t.get("id") == request.tenant_id for t in tenants):
            raise HTTPException(status_code=400, detail="El ID del Tenant ya existe")
            
        new_tenant = request.dict()
        new_tenant["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        tenants.append(new_tenant)
        
        with open(tenants_file, 'w', encoding='utf-8-sig') as f:
            json.dump(tenants, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "message": "Tenant creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenants")
async def get_tenants():
    try:
        tenants_file = DATA_DIR / "tenants.json"
        if not tenants_file.exists():
            return {"status": "success", "tenants": []}
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            tenants = json.load(f)
        return {"status": "success", "tenants": tenants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, request: TenantCreateRequest):
    try:
        tenants_file = DATA_DIR / "tenants.json"
        if not tenants_file.exists():
            raise HTTPException(status_code=404, detail="No hay tenants")
        with open(tenants_file, 'r', encoding='utf-8-sig') as f:
            tenants = json.load(f)
        tenant_idx = next((i for i, t in enumerate(tenants) if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
        if tenant_idx is None:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        tenants[tenant_idx].update({
            "company_name": request.company_name,
            "industry": request.industry,
            "system_prompt": request.system_prompt,
            "main_objective": request.main_objective,
            "escalation_email": request.escalation_email,
            "updated_at": datetime.now().isoformat()
        })
        with open(tenants_file, 'w', encoding='utf-8-sig') as f:
            json.dump(tenants, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Tenant actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
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
        tenant_dir = DATA_DIR / "websites" / tenant_id
        if tenant_dir.exists():
            import shutil
            shutil.rmtree(tenant_dir)
        return {"status": "success", "message": "Tenant eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenant/{tenant_id}/details")
async def get_tenant_details(tenant_id: str):
    try:
        tenants_file = DATA_DIR / "tenants.json"
        tenant_info = None
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                tenants = json.load(f)
                tenant_info = next((t for t in tenants if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
        leads = rag_service.storage.get_leads_by_tenant(tenant_id)
        conversations = rag_service.storage.get_conversations_by_tenant(tenant_id)
        unique_sessions = len(set(c.get("session_id", "unknown") for c in conversations if c.get("tenant_id") == tenant_id))
        return {
            "status": "success",
            "tenant": tenant_info,
            "stats": {
                "total_leads": len(leads),
                "total_conversations": len(conversations),
                "unique_sessions": unique_sessions,
                "conversion_rate": round((len(leads) / unique_sessions * 100), 1) if unique_sessions > 0 else 0
            },
            "leads": leads[-10:],
            "recent_conversations": conversations[-5:]
        }
    except Exception as e:
        logger.error(f"Error obteniendo detalles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    try:
        all_leads = rag_service.storage.get_all_leads()
        all_convs = rag_service.storage.get_all_conversations() if hasattr(rag_service.storage, 'get_all_conversations') else []
        tenants_file = DATA_DIR / "tenants.json"
        active_tenants = 0
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                active_tenants = len(json.load(f))
        conversion_rate = round((len(all_leads) / len(all_convs)) * 100, 1) if len(all_convs) > 0 else 0
        return {
            "status": "success",
            "metrics": {
                "total_conversations": len(all_convs),
                "total_leads": len(all_leads),
                "conversion_rate": conversion_rate,
                "active_tenants": active_tenants
            }
        }
    except Exception as e:
        return {"status": "success", "metrics": {"total_conversations": 0, "total_leads": 0, "conversion_rate": 0, "active_tenants": 0}}

@app.post("/api/generate/{tenant_id}")
async def generate_service(tenant_id: str, request: WebsiteGenerationRequest):
    try:
        result = await website_service.generate_modular_service(
            tenant_id=tenant_id, industry=request.industry, objective=request.objective,
            audience=request.audience, tone=request.tone, package=request.package
        )
        return result
    except Exception as e:
        logger.error(f"Error generando servicio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload/{tenant_id}")
async def upload_document(tenant_id: str, file: UploadFile = File(...)):
    try:
        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id / "documents"
        tenant_docs_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_docs_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        chunks = await rag_service.process_document(tenant_id, file_path)
        return {"status": "success", "filename": file.filename, "chunks_indexed": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{tenant_id}")
async def chat_with_bot(tenant_id: str, request: dict):
    try:
        question = request.get("question", "")
        session_id = request.get("session_id", "default")
        if not question:
            raise HTTPException(status_code=400, detail="Pregunta requerida")
        result = await rag_service.query(tenant_id, question, session_id)
        return {"status": "success", "answer": result["answer"], "is_lead": result["is_lead"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/websites/{tenant_id}/content")
async def update_website_content(tenant_id: str, content: dict):
    try:
        result = await website_service.regenerate_website(tenant_id, content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ===== GUARDAR PLANTILLAS DIRECTAMENTE =====
@app.post("/api/chatbot/save-templates/{tenant_id}")
async def save_chatbot_templates(tenant_id: str, templates: dict):
    try:
        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id / "documents"
        tenant_docs_dir.mkdir(parents=True, exist_ok=True)
        
        chunks_total = 0
        
        # Guardar Catálogo
        if templates.get("catalogo"):
            cat_path = tenant_docs_dir / "catalogo.txt"
            with open(cat_path, "w", encoding="utf-8-sig") as f:
                f.write(templates["catalogo"])
            chunks = await rag_service.process_document(tenant_id, cat_path)
            chunks_total += chunks
        
        # Guardar Políticas
        if templates.get("politicas"):
            pol_path = tenant_docs_dir / "politicas.txt"
            with open(pol_path, "w", encoding="utf-8-sig") as f:
                f.write(templates["politicas"])
            chunks = await rag_service.process_document(tenant_id, pol_path)
            chunks_total += chunks
        
        # Guardar FAQs
        if templates.get("faqs"):
            faq_path = tenant_docs_dir / "faqs.txt"
            with open(faq_path, "w", encoding="utf-8-sig") as f:
                f.write(templates["faqs"])
            chunks = await rag_service.process_document(tenant_id, faq_path)
            chunks_total += chunks
        
        return {
            "status": "success",
            "message": "Plantillas guardadas y procesadas",
            "chunks_indexed": chunks_total,
            "files_created": {
                "catalogo": bool(templates.get("catalogo")),
                "politicas": bool(templates.get("politicas")),
                "faqs": bool(templates.get("faqs"))
            }
        }
    except Exception as e:
        logger.error(f"Error guardando plantillas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== GENERADOR DE CONTENIDO PARA REDES SOCIALES =====
@app.post("/api/social/generate/{tenant_id}")
async def generate_social_content(tenant_id: str):
    try:
        # 1. Obtener datos del tenant
        tenants_file = DATA_DIR / "tenants.json"
        tenant_info = None
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                tenants = json.load(f)
                tenant_info = next((t for t in tenants if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
        
        if not tenant_info:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        industry = tenant_info.get("industry", "negocio general")
        company_name = tenant_info.get("company_name", "nuestra empresa")
        
        # 2. Prompt para la IA
        prompt = f"""
        Eres un experto en marketing digital y copywriting para redes sociales.
        Genera contenido atractivo y profesional para la empresa "{company_name}" que se dedica a la industria de "{industry}".
        
        Devuelve SOLO un objeto JSON válido (sin markdown) con la siguiente estructura exacta:
        {{
            "linkedin": [
                {{"title": "Título profesional y llamativo", "body": "Texto del post de LinkedIn (3-4 párrafos, tono profesional, enfocado en valor y liderazgo de pensamiento)", "hashtags": "#Hashtag1 #Hashtag2 #Hashtag3"}},
                {{"title": "Título sobre tendencias del sector", "body": "Texto del post de LinkedIn (3-4 párrafos, tono profesional)", "hashtags": "#Hashtag1 #Hashtag2 #Hashtag3"}},
                {{"title": "Título sobre casos de éxito o beneficios", "body": "Texto del post de LinkedIn (3-4 párrafos, tono profesional)", "hashtags": "#Hashtag1 #Hashtag2 #Hashtag3"}}
            ],
            "twitter": [
                {{"text": "Tweet corto, directo y con gancho (máx 280 caracteres)", "hashtags": "#Hashtag1 #Hashtag2"}},
                {{"text": "Tweet con pregunta para generar interacción (máx 280 caracteres)", "hashtags": "#Hashtag1 #Hashtag2"}},
                {{"text": "Tweet con dato curioso o tip rápido del sector (máx 280 caracteres)", "hashtags": "#Hashtag1 #Hashtag2"}}
            ],
            "instagram": {{"caption": "Texto atractivo para Instagram con emojis, llamado a la acción y salto de líneas", "hashtags": "#Hashtag1 #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5"}}
        }}
        """
        
        # 3. Llamar a la IA
        response = await website_service.llm_service.generate_content(prompt, max_tokens=1500, temperature=0.8)
        response = response.replace("```json", "").replace("```", "").strip()
        
        try:
            content = json.loads(response)
        except json.JSONDecodeError:
            raise Exception("La IA no generó un JSON válido.")
            
        return {"status": "success", "content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando contenido social: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{tenant_id}")
async def get_analytics(tenant_id: str, days: int = 30):
    """Dashboard de métricas para un tenant específico"""
    try:
        # Obtener conversaciones del tenant
        conversations = rag_service.storage.get_conversations_by_tenant(tenant_id)
        leads = rag_service.storage.get_leads_by_tenant(tenant_id)
        
        # Filtrar por período (últimos X días)
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_convs = [c for c in conversations if datetime.fromisoformat(c.get("timestamp", c.get("captured_at", datetime.now().isoformat()))) >= cutoff_date]
        recent_leads = [l for l in leads if datetime.fromisoformat(l.get("captured_at", datetime.now().isoformat())) >= cutoff_date]
        
        # Métricas principales
        total_conversations = len(recent_convs)
        total_leads = len(recent_leads)
        conversion_rate = round((total_leads / total_conversations * 100), 1) if total_conversations > 0 else 0
        
        # Conversaciones por día (últimos 7 días)
        daily_convs = defaultdict(int)
        daily_leads = defaultdict(int)
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_convs[day] = 0
            daily_leads[day] = 0
        
        for conv in recent_convs:
            try:
                day = datetime.fromisoformat(conv.get("timestamp", conv.get("captured_at"))).strftime("%Y-%m-%d")
                if day in daily_convs:
                    daily_convs[day] += 1
                    if conv.get("is_lead"):
                        daily_leads[day] += 1
            except:
                pass
        
        # Preguntas más frecuentes
        questions = [c.get("question", "").lower() for c in recent_convs if c.get("question")]
        # Extraer palabras clave (simplificado)
        keywords = []
        for q in questions:
            keywords.extend([w for w in q.split() if len(w) > 4 and w not in ["tienes", "puedo", "cuanto", "donde", "cuando", "como", "hacen", "precio", "sobre", "ustedes"]])
        
        top_keywords = Counter(keywords).most_common(5)
        
        # Últimos leads capturados
        recent_leads_list = sorted(recent_leads, key=lambda x: x.get("captured_at", ""), reverse=True)[:5]
        
        return {
            "status": "success",
            "period": f"Últimos {days} días",
            "metrics": {
                "total_conversations": total_conversations,
                "total_leads": total_leads,
                "conversion_rate": conversion_rate,
                "avg_daily_conversations": round(total_conversations / days, 1) if days > 0 else 0,
                "lead_quality_score": "Alta" if conversion_rate > 5 else "Media" if conversion_rate > 2 else "Baja"
            },
            "daily_chart": {
                "labels": list(daily_convs.keys())[::-1],
                "conversations": list(daily_convs.values())[::-1],
                "leads": list(daily_leads.values())[::-1]
            },
            "top_questions": [
                {"word": word, "count": count} for word, count in top_keywords
            ],
            "recent_leads": recent_leads_list
        }
    except Exception as e:
        logger.error(f"Error en analytics: {e}")
        return {
            "status": "error",
            "metrics": {"total_conversations": 0, "total_leads": 0, "conversion_rate": 0},
            "daily_chart": {"labels": [], "conversations": [], "leads": []},
            "top_questions": [],
            "recent_leads": []
        }

@app.get("/api/analytics/global")
async def get_global_analytics():
    """Métricas globales de TODAS las empresas (para ti como admin)"""
    try:
        all_convs = rag_service.storage.get_all_conversations() if hasattr(rag_service.storage, 'get_all_conversations') else []
        all_leads = rag_service.storage.get_all_leads()
        
        # Contar tenants activos
        tenants_file = DATA_DIR / "tenants.json"
        active_tenants = 0
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                active_tenants = len(json.load(f))
        
        # Ingresos estimados (basado en paquetes)
        revenue_estimate = 0
        if tenants_file.exists():
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                tenants = json.load(f)
                package_prices = {"full": 499, "web_chat": 299, "chat_only": 99, "seo_only": 149}
                for t in tenants:
                    revenue_estimate += package_prices.get(t.get("package", "full"), 299)
        
        conversion_rate = round((len(all_leads) / len(all_convs) * 100), 1) if len(all_convs) > 0 else 0
        
        return {
            "status": "success",
            "metrics": {
                "total_tenants": active_tenants,
                "total_conversations": len(all_convs),
                "total_leads": len(all_leads),
                "conversion_rate": conversion_rate,
                "monthly_revenue_estimate": revenue_estimate,
                "yearly_revenue_estimate": revenue_estimate * 12
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "metrics": {
                "total_tenants": 0,
                "total_conversations": 0,
                "total_leads": 0,
                "conversion_rate": 0,
                "monthly_revenue_estimate": 0,
                "yearly_revenue_estimate": 0
            }
        }
 from app.services.export_service import ExportService

# ============================================
# EXPORTADOR DE SITIOS WEB
# ============================================
@app.post("/api/export/{tenant_id}")
async def export_site(tenant_id: str):
    """Exporta el sitio web completo en ZIP"""
    result = ExportService.export_site(tenant_id)
    return result       
        
        