import hashlib
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import DATA_DIR, check_rate_limit, read_json_file, require_admin, write_json_atomic
from app.schemas import LeadUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

LEADS_FILE = DATA_DIR / "storage" / "leads.json"
TENANTS_FILE = DATA_DIR / "tenants.json"

VALID_STATUSES = {"nuevo", "contactado", "convertido"}


def _lead_id(lead: dict) -> str:
    """Devuelve el id del lead, generando uno estable si no existe (leads viejos)"""
    lead_id = lead.get("id") or lead.get("lead_id")
    if lead_id:
        return str(lead_id)
    seed = f"{lead.get('email', '')}|{lead.get('tenant_id', '')}|{lead.get('timestamp', '')}"
    return hashlib.sha1(seed.encode()).hexdigest()[:12]


def _enrich_lead(lead: dict, company_map: dict) -> dict:
    return {
        "id": _lead_id(lead),
        "tenant_id": lead.get("tenant_id", ""),
        "email": lead.get("email", ""),
        "question": lead.get("question", ""),
        "source": lead.get("source", ""),
        "status": lead.get("status", "nuevo"),
        "timestamp": lead.get("timestamp", ""),
        "company": company_map.get(lead.get("tenant_id", ""), lead.get("tenant_id", "")),
    }


@router.get("/api/leads")
async def list_leads(q: str = "", status: str = "", page: int = 1, per_page: int = 20, current_user: dict = Depends(require_admin)):
    """Listar leads con busqueda, filtro por estado y paginacion (solo admin)"""
    try:
        leads = read_json_file(LEADS_FILE, [])
        tenants = read_json_file(TENANTS_FILE, [])
        company_map = {
            (t.get("tenant_id") or t.get("id")): t.get("company_name", t.get("tenant_id", ""))
            for t in tenants
        }

        result = [_enrich_lead(l, company_map) for l in leads]

        counts = {
            "total": len(result),
            "nuevo": sum(1 for l in result if l["status"] == "nuevo"),
            "contactado": sum(1 for l in result if l["status"] == "contactado"),
            "convertido": sum(1 for l in result if l["status"] == "convertido"),
        }

        if status:
            result = [l for l in result if l["status"] == status]

        if q:
            ql = q.strip().lower()
            result = [
                l for l in result
                if ql in l["email"].lower() or ql in l["company"].lower()
            ]

        result.sort(key=lambda l: l.get("timestamp", ""), reverse=True)

        total_filtered = len(result)
        page = max(1, page)
        per_page = min(max(1, per_page), 100)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = result[start:end]

        return {
            "status": "success",
            "leads": paginated,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_filtered,
                "total_pages": max(1, -(-total_filtered // per_page)),
            },
            "counts": counts,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/contact")
async def contact_form(request: Request):
    """Formulario de contacto publico - crea un lead (rate limit 5/min por IP)"""
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"contact:{client_ip}", limit=5, window_seconds=60):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intenta en un minuto.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalido")

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    phone = (body.get("phone") or "").strip()
    message = (body.get("message") or "").strip()
    tenant_id = (body.get("tenant_id") or "").strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalido")
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje es obligatorio")

    lead = {
        "id": hashlib.sha1(f"{email}|{tenant_id}|{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        "tenant_id": tenant_id,
        "email": email,
        "name": name,
        "phone": phone,
        "question": message,
        "source": "contact_form",
        "status": "nuevo",
        "timestamp": datetime.now().isoformat(),
    }

    leads = read_json_file(LEADS_FILE, [])

    # Deduplicar: si ya existe un lead con el mismo email y tenant en los ultimos 5 min
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
    for existing in leads:
        if (existing.get("email") == email
                and existing.get("tenant_id") == tenant_id
                and existing.get("timestamp", "") > cutoff):
            return {"status": "success", "message": "Ya recibimos tu mensaje. Te contactaremos pronto."}

    leads.append(lead)
    write_json_atomic(LEADS_FILE, leads)

    logger.info(f"✅ Lead de contacto: {email} ({name}) → tenant={tenant_id}")
    return {"status": "success", "message": "¡Gracias! Te contactaremos pronto."}


@router.patch("/api/leads/{lead_id}")
async def update_lead(lead_id: str, body: LeadUpdate, current_user: dict = Depends(require_admin)):
    """Actualizar el estado de un lead: nuevo / contactado / convertido (solo admin)"""
    try:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Estado invalido. Usa: nuevo, contactado, convertido")

        leads = read_json_file(LEADS_FILE, [])
        updated = False
        for lead in leads:
            if _lead_id(lead) == lead_id:
                lead["status"] = body.status
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        write_json_atomic(LEADS_FILE, leads)
        return {"status": "success", "message": f"Lead marcado como {body.status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))
