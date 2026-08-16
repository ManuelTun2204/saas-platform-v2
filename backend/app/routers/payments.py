import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.schemas import CheckoutRequest
from app.deps import DATA_DIR, auth_service, check_rate_limit, payment_service, templates, validate_tenant_id

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
    """Crear orden + redirección al checkout. El tenant se crea solo tras el pago confirmado."""
    try:
        provider = request.provider
        valid_providers = [p["id"] for p in payment_service.get_available_providers()]
        if provider not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Metodo de pago no disponible. Opciones: {', '.join(valid_providers)}")

        tenant_id = validate_tenant_id(request.tenant_id)

        site_config = {
            "company_name": request.company_name,
            "industry": request.industry,
            "system_prompt": request.system_prompt,
            "main_objective": request.main_objective,
            "escalation_email": request.escalation_email,
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
        order = payment_service.create_order(tenant_id, request.package, provider, site_config)
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


@router.get("/api/payments/orders")
async def list_payment_orders(current_user: dict = Depends(auth_service.get_current_user)):
    """Lista de todas las ordenes de pago (solo admin)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        return {"status": "success", "orders": payment_service.list_orders()}
    except Exception as e:
        logger.error(f"Error listando ordenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/payments/cancel/{order_id}")
async def cancel_payment_order(order_id: str):
    """Marca una orden no pagada como cancelada (publico para la pagina de cancelacion)"""
    try:
        return payment_service.cancel_order(order_id)
    except Exception as e:
        logger.error(f"Error cancelando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/payments/webhook/stripe")
async def stripe_webhook(http_request: Request):
    """Webhook de Stripe: confirma el pago y genera la entrega"""
    raw = await http_request.body()
    signature = http_request.headers.get("stripe-signature", "")
    try:
        return await payment_service.handle_stripe_webhook(raw, signature)
    except Exception as e:
        logger.error(f"Error en webhook de Stripe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/payments/webhook/mercadopago")
async def mercadopago_webhook(http_request: Request):
    """Webhook de Mercado Pago: confirma el pago y genera la entrega"""
    raw = await http_request.body()
    try:
        return await payment_service.handle_mp_webhook(raw)
    except Exception as e:
        logger.error(f"Error en webhook de Mercado Pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/payments/webhook/paypal")
async def paypal_webhook(http_request: Request):
    """Webhook de PayPal: confirma el pago y genera la entrega"""
    raw = await http_request.body()
    try:
        return await payment_service.handle_paypal_webhook(raw)
    except Exception as e:
        logger.error(f"Error en webhook de PayPal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkout-return", response_class=HTMLResponse)
async def checkout_return_page(request: Request):
    """Pagina que confirma el pago y dispara la generacion"""
    return templates.TemplateResponse("checkout_return.html", {"request": request, "message": "Verificando pago"})


@router.get("/checkout-cancel", response_class=HTMLResponse)
async def checkout_cancel_page(request: Request, order_id: str = ""):
    """Pagina de pago cancelado"""
    return templates.TemplateResponse("checkout_cancel.html", {"request": request, "order_id": order_id, "message": "Pago cancelado"})
