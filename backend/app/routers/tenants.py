import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.schemas import ChatRequest, TenantCreateRequest, WebsiteGenerationRequest
from app.deps import DATA_DIR, check_rate_limit, create_tenant_record, export_service, rag_service, read_json_file, require_admin, website_service, write_json_atomic

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/api/tenants")
async def create_tenant(request: TenantCreateRequest, current_user: dict = Depends(require_admin)):
    """Crear nuevo tenant (solo admin)"""
    try:
        create_tenant_record(request.dict())
        return {"status": "success", "message": "Tenant creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tenants")
async def get_tenants(current_user: dict = Depends(require_admin)):
    """Listar todos los tenants (solo admin)"""
    try:
        return {"status": "success", "tenants": read_json_file(DATA_DIR / "tenants.json", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, current_user: dict = Depends(require_admin)):
    """Eliminar tenant (solo admin)"""
    try:
        tenants = read_json_file(DATA_DIR / "tenants.json", [])
        new_tenants = [t for t in tenants if t.get("tenant_id") != tenant_id and t.get("id") != tenant_id]
        if len(new_tenants) == len(tenants):
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        write_json_atomic(DATA_DIR / "tenants.json", new_tenants)

        tenant_dir = DATA_DIR / "websites" / tenant_id
        if tenant_dir.exists():
            shutil.rmtree(tenant_dir)

        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id
        if tenant_docs_dir.exists():
            shutil.rmtree(tenant_docs_dir)

        return {"status": "success", "message": "Tenant eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/generate/{tenant_id}")
async def generate_service(tenant_id: str, request: WebsiteGenerationRequest, current_user: dict = Depends(require_admin)):
    """Generar sitio web con IA (solo admin)"""
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


@router.post("/api/documents/upload/{tenant_id}")
async def upload_document(tenant_id: str, file: UploadFile = File(...), http_request: Request = None, current_user: dict = Depends(require_admin)):
    """Subir documento para el chatbot RAG (solo admin, max 10 MB)"""
    try:
        safe_name = os.path.basename(file.filename or "")
        if not safe_name.lower().endswith(('.txt', '.pdf')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt y .pdf")
        if len(safe_name) > 120:
            raise HTTPException(status_code=400, detail="El nombre del archivo es demasiado largo")

        # Validar tamaño ANTES de leer todo el archivo (evita llenar la memoria)
        content_length = http_request.headers.get("content-length") if http_request else None
        if content_length and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="El archivo excede el limite de 10 MB")

        content = b""
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            content += chunk
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="El archivo excede el limite de 10 MB")

        tenant_docs_dir = DATA_DIR / "tenants" / tenant_id / "documents"
        tenant_docs_dir.mkdir(parents=True, exist_ok=True)

        file_path = tenant_docs_dir / safe_name
        with open(file_path, 'wb') as f:
            f.write(content)

        if safe_name.lower().endswith(('.txt', '.pdf')):
            chunks_indexed = await rag_service.process_document(tenant_id, str(file_path))
        else:
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


@router.post("/api/chat/{tenant_id}")
async def chat_endpoint(tenant_id: str, request: ChatRequest, http_request: Request):
    """Endpoint para el chatbot"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not check_rate_limit(f"chat:{tenant_id}:{client_ip}", limit=20, window_seconds=60):
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intenta nuevamente en un momento.")

        question = request.question
        session_id = (request.session_id or "default")[:100]
        user_email = request.email

        answer = await rag_service.query(tenant_id, question, session_id=session_id)

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        detected_email = re.search(email_pattern, question)
        if detected_email:
            user_email = detected_email.group()

        if user_email:
            lead_data = {
                "tenant_id": tenant_id,
                "email": user_email,
                "question": question,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

            leads_file = DATA_DIR / "storage" / "leads.json"
            leads_file.parent.mkdir(exist_ok=True)
            leads = read_json_file(leads_file, [])

            if not any(l.get("email") == user_email and l.get("tenant_id") == tenant_id for l in leads):
                leads.append(lead_data)
                write_json_atomic(leads_file, leads)

                try:
                    from app.deps import email_service
                    tenant_info = next((t for t in read_json_file(DATA_DIR / "tenants.json", []) if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
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


@router.get("/api/tenant/{tenant_id}/details")
async def get_tenant_details(tenant_id: str, current_user: dict = Depends(require_admin)):
    """Obtener detalles de un tenant (solo admin)"""
    try:
        tenants = read_json_file(DATA_DIR / "tenants.json", [])
        tenant = next((t for t in tenants if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        return {"status": "success", "tenant": tenant}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/export/{tenant_id}")
async def export_site(tenant_id: str, current_user: dict = Depends(require_admin)):
    """Exportar sitio web como ZIP (solo admin)"""
    try:
        return export_service.export_site(tenant_id)
    except Exception as e:
        logger.error(f"Error exportando sitio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/site-editor/{tenant_id}")
async def get_site_editor_data(tenant_id: str, current_user: dict = Depends(require_admin)):
    """Obtener datos editables del sitio (solo admin)"""
    try:
        site_data_file = DATA_DIR / "websites" / tenant_id / "site_data.json"
        if not site_data_file.exists():
            raise HTTPException(status_code=404, detail="Sitio no encontrado")
        site_data = read_json_file(site_data_file, {})

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


@router.post("/api/site-editor/{tenant_id}")
async def save_site_editor_data(tenant_id: str, data: dict, current_user: dict = Depends(require_admin)):
    """Guardar cambios del editor y regenerar sitio (solo admin)"""
    try:
        site_data_file = DATA_DIR / "websites" / tenant_id / "site_data.json"
        if not site_data_file.exists():
            raise HTTPException(status_code=404, detail="Sitio no encontrado")

        site_data = read_json_file(site_data_file, {})
        for key in data:
            if key in site_data:
                site_data[key] = data[key]

        write_json_atomic(site_data_file, site_data)

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
