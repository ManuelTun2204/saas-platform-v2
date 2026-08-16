import collections
import json
import logging
import re
import time
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.templating import Jinja2Templates

from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.email_service import EmailService
from app.services.website_service import WebsiteService
from app.services.export_service import ExportService
from app.services.auth_service import auth_service
from app.services.payment_service import payment_service, PRICES

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Instancias compartidas de servicios
llm_service = LLMService()
rag_service = RAGService()
email_service = EmailService()
website_service = WebsiteService()
export_service = ExportService()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

_RATE_BUCKETS = {}


def check_rate_limit(key: str, limit: int, window_seconds: int, consume: bool = True) -> bool:
    now = time.time()
    bucket = _RATE_BUCKETS.setdefault(key, collections.deque())
    while bucket and bucket[0] < now - window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    if consume:
        bucket.append(now)
    return True


def require_admin(current_user: dict = Depends(auth_service.get_current_user)):
    """Dependencia que exige rol de administrador"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta accion")
    return current_user


def write_json_atomic(path: Path, data):
    """Escribe JSON de forma atomica (temp + renombre) para evitar archivos corruptos con multiples workers"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def validate_tenant_id(tenant_id: str) -> str:
    """Valida el ID de tenant y devuelve el valor normalizado. Lanza HTTPException si falla."""
    tenant_id = (tenant_id or "").strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id es requerido")
    if len(tenant_id) < 3 or len(tenant_id) > 63:
        raise HTTPException(status_code=400, detail="tenant_id debe tener entre 3 y 63 caracteres")
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', tenant_id):
        raise HTTPException(
            status_code=400,
            detail="tenant_id inválido. Solo letras, números, guiones (-) y guiones bajos (_). Sin espacios. Ej: 'dulce-demo'"
        )
    return tenant_id


def create_tenant_record(tenant_data: dict) -> dict:
    """Crea un tenant en tenants.json validando el ID. Lanza HTTPException si falla."""
    tenant_id = validate_tenant_id(tenant_data.get("tenant_id"))
    tenants_file = DATA_DIR / "tenants.json"
    tenants = []
    if tenants_file.exists():
        try:
            with open(tenants_file, 'r', encoding='utf-8-sig') as f:
                loaded = json.load(f)
            # Robustez: si el archivo esta vacio ({}) o es invalido, empezar de cero
            if isinstance(loaded, list):
                tenants = loaded
        except Exception:
            pass
    if any(t.get("tenant_id") == tenant_id or t.get("id") == tenant_id for t in tenants):
        raise HTTPException(status_code=400, detail="El ID del Tenant ya existe")
    new_tenant = dict(tenant_data)
    new_tenant["tenant_id"] = tenant_id
    new_tenant["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    new_tenant["payment_status"] = "pending"
    tenants.append(new_tenant)
    write_json_atomic(tenants_file, tenants)
    return new_tenant


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:
        return default
