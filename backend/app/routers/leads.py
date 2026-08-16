import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.deps import DATA_DIR, read_json_file, require_admin, write_json_atomic
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
async def list_leads(q: str = "", status: str = "", current_user: dict = Depends(require_admin)):
    """Listar leads con busqueda y filtro por estado (solo admin)"""
    try:
        leads = read_json_file(LEADS_FILE, [])
        tenants = read_json_file(TENANTS_FILE, [])
        company_map = {
            (t.get("tenant_id") or t.get("id")): t.get("company_name", t.get("tenant_id", ""))
            for t in tenants
        }

        result = [_enrich_lead(l, company_map) for l in leads]

        if status:
            result = [l for l in result if l["status"] == status]

        if q:
            ql = q.strip().lower()
            result = [
                l for l in result
                if ql in l["email"].lower() or ql in l["company"].lower()
            ]

        result.sort(key=lambda l: l.get("timestamp", ""), reverse=True)

        return {
            "status": "success",
            "leads": result,
            "counts": {
                "total": len(leads),
                "nuevo": sum(1 for l in result if l["status"] == "nuevo"),
                "contactado": sum(1 for l in result if l["status"] == "contactado"),
                "convertido": sum(1 for l in result if l["status"] == "convertido"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
