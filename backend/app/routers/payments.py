import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.schemas import CheckoutRequest
from app.deps import DATA_DIR, auth_service, check_rate_limit, create_tenant_record, payment_service, templates

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/payments/config")
async def payments_config():
    """Configuración de pagos: pasarelas disponibles y precios de paquetes"""
    return {
        "status": "success",
        "currency": "USD",
        "providers": payment_service.get_available_providers(),
        "packages": payment_service.get_packages(),
    }


@router.post("/api/payments/checkout")
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
        create_tenant_record(tenant_data)

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


@router.get("/api/payments/status/{order_id}")
async def get_payment_status(order_id: str, http_request: Request):
    """Consulta el estado de una orden (publico para el checkout, con rate limit)"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(f"paystatus:{order_id}:{client_ip}", limit=60, window_seconds=60):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes.")
    try:
        return await payment_service.get_order_status(order_id)
    except Exception as e:
        logger.error(f"Error consultando estado de pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/payments/finalize/{order_id}")
async def finalize_payment(order_id: str, http_request: Request):
    """Genera la entrega cuando la orden esta pagada (publico para el checkout, idempotente)"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(f"payfinalize:{order_id}:{client_ip}", limit=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes.")
    try:
        return await payment_service.finalize(order_id)
    except Exception as e:
        logger.error(f"Error finalizando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkout-return", response_class=HTMLResponse)
async def checkout_return_page(request: Request):
    """Pagina que confirma el pago y dispara la generacion"""
    return templates.TemplateResponse("checkout_return.html", {"request": request, "message": "Verificando pago"})


@router.get("/checkout-cancel", response_class=HTMLResponse)
async def checkout_cancel_page(request: Request):
    """Pagina de pago cancelado"""
    return templates.TemplateResponse("checkout_cancel.html", {"request": request, "message": "Pago cancelado"})
