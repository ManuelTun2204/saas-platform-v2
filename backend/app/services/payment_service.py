import os
import json
import logging
import time
import secrets
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ORDERS_FILE = DATA_DIR / "storage" / "orders.json"
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")
CURRENCY = "USD"

PRICES = {
    "full": int(os.getenv("PRICE_FULL", "399")),
    "web_chat": int(os.getenv("PRICE_WEB_CHAT", "249")),
    "chat_only": int(os.getenv("PRICE_CHAT_ONLY", "99")),
    "seo_only": int(os.getenv("PRICE_SEO_ONLY", "99")),
}
PACKAGES = {
    "full": "Full Service",
    "web_chat": "Web + Chat",
    "chat_only": "Solo Chatbot",
    "seo_only": "SEO Only",
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_API_BASE = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")

_DEMO_PROVIDER = {"id": "demo", "name": "Demo (pago simulado)", "test": True}


def _read_orders():
    orders = []
    if ORDERS_FILE.exists():
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8-sig") as f:
                orders = json.load(f)
        except Exception:
            orders = []
    return orders


def _write_orders(orders):
    ORDERS_FILE.parent.mkdir(exist_ok=True)
    with open(ORDERS_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)


def _get_order(order_id):
    for o in _read_orders():
        if o.get("order_id") == order_id:
            return o
    return None


def _update_order(order_id, updates):
    orders = _read_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            o.update(updates)
            o["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _write_orders(orders)


class PaymentService:

    def get_available_providers(self):
        providers = []
        if STRIPE_SECRET_KEY:
            providers.append({
                "id": "stripe",
                "name": "Stripe (Tarjeta)",
                "test": STRIPE_SECRET_KEY.startswith("sk_test_"),
            })
        if MP_ACCESS_TOKEN:
            providers.append({
                "id": "mercadopago",
                "name": "Mercado Pago",
                "test": MP_ACCESS_TOKEN.startswith("TEST-"),
            })
        if PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET:
            providers.append({
                "id": "paypal",
                "name": "PayPal",
                "test": "sandbox" in PAYPAL_API_BASE,
            })
        if not providers:
            return [_DEMO_PROVIDER]

        allowed = [p.strip() for p in os.getenv("PAYMENT_PROVIDERS", "all").split(",") if p.strip()]
        if "all" not in allowed:
            providers = [p for p in providers if p["id"] in allowed]
            if not providers:
                providers = [_DEMO_PROVIDER]
        return providers

    def get_packages(self):
        return [
            {"id": "full", "name": PACKAGES["full"], "price": PRICES["full"]},
            {"id": "web_chat", "name": PACKAGES["web_chat"], "price": PRICES["web_chat"]},
            {"id": "chat_only", "name": PACKAGES["chat_only"], "price": PRICES["chat_only"]},
        ]

    def create_order(self, tenant_id, package, provider, site_config):
        order = {
            "order_id": "ord_" + secrets.token_hex(8),
            "tenant_id": tenant_id,
            "package": package,
            "amount": PRICES.get(package, 0),
            "currency": CURRENCY,
            "provider": provider,
            "status": "pending",
            "provider_id": "",
            "site_config": site_config,
            "generated": False,
            "preview_url": "",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        orders = _read_orders()
        orders.append(order)
        _write_orders(orders)
        return order

    async def create_checkout(self, order):
        provider = order["provider"]
        if provider == "demo":
            _update_order(order["order_id"], {"status": "paid", "provider_id": "demo"})
            return f"{PUBLIC_URL}/checkout-return?order_id={order['order_id']}&provider=demo"
        if provider == "stripe":
            return await self._stripe_create_session(order)
        if provider == "mercadopago":
            return await self._mp_create_preference(order)
        if provider == "paypal":
            return await self._paypal_create_order(order)
        raise ValueError(f"Proveedor de pago desconocido: {provider}")

    async def _stripe_create_session(self, order):
        url = "https://api.stripe.com/v1/checkout/sessions"
        data = {
            "mode": "payment",
            "success_url": f"{PUBLIC_URL}/checkout-return?order_id={order['order_id']}&provider=stripe",
            "cancel_url": f"{PUBLIC_URL}/checkout-cancel?order_id={order['order_id']}",
            "client_reference_id": order["order_id"],
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": order["currency"].lower(),
            "line_items[0][price_data][product_data][name]": PACKAGES.get(order["package"], order["package"]),
            "line_items[0][price_data][unit_amount]": str(int(order["amount"] * 100)),
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                data=data,
                timeout=30,
            )
        if r.status_code >= 400:
            logger.error(f"Stripe error: {r.text}")
            raise ValueError("Error creando la sesion de pago de Stripe")
        session = r.json()
        _update_order(order["order_id"], {"provider_id": session.get("id", "")})
        return session["url"]

    async def _mp_create_preference(self, order):
        url = "https://api.mercadopago.com/checkout/preferences"
        payload = {
            "items": [{
                "title": PACKAGES.get(order["package"], order["package"]),
                "quantity": 1,
                "unit_price": float(order["amount"]),
                "currency_id": order["currency"],
            }],
            "external_reference": order["order_id"],
            "auto_return": "approved",
            "back_urls": {
                "success": f"{PUBLIC_URL}/checkout-return?order_id={order['order_id']}&provider=mercadopago",
                "failure": f"{PUBLIC_URL}/checkout-cancel?order_id={order['order_id']}",
                "pending": f"{PUBLIC_URL}/checkout-return?order_id={order['order_id']}&provider=mercadopago",
            },
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                json=payload,
                timeout=30,
            )
        if r.status_code >= 400:
            logger.error(f"MercadoPago error: {r.text}")
            raise ValueError("Error creando la preferencia de Mercado Pago")
        pref = r.json()
        _update_order(order["order_id"], {"provider_id": pref.get("id", "")})
        return pref["init_point"]

    async def _paypal_create_order(self, order):
        token = await self._paypal_token()
        url = f"{PAYPAL_API_BASE}/v2/checkout/orders"
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": order["order_id"],
                "amount": {
                    "currency_code": order["currency"],
                    "value": f"{order['amount']:.2f}",
                },
            }],
            "application_context": {
                "return_url": f"{PUBLIC_URL}/checkout-return?order_id={order['order_id']}&provider=paypal",
                "cancel_url": f"{PUBLIC_URL}/checkout-cancel?order_id={order['order_id']}",
                "user_action": "PAY_NOW",
            },
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
        if r.status_code >= 400:
            logger.error(f"PayPal error: {r.text}")
            raise ValueError("Error creando la orden de PayPal")
        order_resp = r.json()
        _update_order(order["order_id"], {"provider_id": order_resp.get("id", "")})
        approve = next((link["href"] for link in order_resp.get("links", []) if link.get("rel") == "approve"), "")
        if not approve:
            raise ValueError("PayPal no devolvio la URL de aprobacion")
        return approve

    async def _paypal_token(self):
        url = f"{PAYPAL_API_BASE}/v1/oauth2/token"
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                headers={"Accept": "application/json"},
                data={"grant_type": "client_credentials"},
                auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
                timeout=30,
            )
        if r.status_code >= 400:
            logger.error(f"PayPal auth error: {r.text}")
            raise ValueError("Error autenticando con PayPal")
        return r.json().get("access_token", "")

    def _status_payload(self, order, status):
        return {
            "order_id": order["order_id"],
            "status": status,
            "package": order["package"],
            "amount": order["amount"],
            "currency": order["currency"],
            "tenant_id": order["tenant_id"],
            "provider": order["provider"],
            "generated": order.get("generated", False),
            "preview_url": order.get("preview_url", ""),
        }

    async def get_order_status(self, order_id):
        order = _get_order(order_id)
        if not order:
            return {"status": "not_found", "detail": "Orden no encontrada"}
        if order["status"] == "paid":
            return self._status_payload(order, "paid")
        if order["status"] == "cancelled":
            return self._status_payload(order, "cancelled")

        provider = order["provider"]
        try:
            if provider == "demo":
                _update_order(order_id, {"status": "paid"})
                order = _get_order(order_id)
                return self._status_payload(order, "paid")
            if provider == "stripe":
                return await self._stripe_check(order)
            if provider == "mercadopago":
                return await self._mp_check(order)
            if provider == "paypal":
                return await self._paypal_check(order)
        except Exception as e:
            logger.error(f"Error verificando pago {provider}: {e}")
            return self._status_payload(order, "pending")
        return self._status_payload(order, "pending")

    async def _stripe_check(self, order):
        session_id = order.get("provider_id")
        if not session_id:
            return self._status_payload(order, "pending")
        url = f"https://api.stripe.com/v1/checkout/sessions/{session_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"}, timeout=30)
        if r.status_code >= 400:
            return self._status_payload(order, "pending")
        session = r.json()
        if session.get("payment_status") == "paid":
            _update_order(order["order_id"], {"status": "paid"})
            order = _get_order(order["order_id"])
            return self._status_payload(order, "paid")
        return self._status_payload(order, "pending")

    async def _mp_check(self, order):
        url = "https://api.mercadopago.com/v1/payments/search"
        async with httpx.AsyncClient() as client:
            r = await client.get(
                url,
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                params={"external_reference": order["order_id"], "sort": "date_created", "criteria": "desc"},
                timeout=30,
            )
        if r.status_code >= 400:
            return self._status_payload(order, "pending")
        results = r.json().get("results", [])
        if results and results[0].get("status") == "approved":
            _update_order(order["order_id"], {"status": "paid"})
            order = _get_order(order["order_id"])
            return self._status_payload(order, "paid")
        return self._status_payload(order, "pending")

    async def _paypal_check(self, order):
        token = await self._paypal_token()
        provider_id = order.get("provider_id")
        if not provider_id:
            return self._status_payload(order, "pending")
        url = f"{PAYPAL_API_BASE}/v2/checkout/orders/{provider_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if r.status_code >= 400:
            return self._status_payload(order, "pending")
        o = r.json()
        status = o.get("status")
        if status == "APPROVED":
            cap_url = f"{PAYPAL_API_BASE}/v2/checkout/orders/{provider_id}/capture"
            async with httpx.AsyncClient() as client:
                r2 = await client.post(
                    cap_url,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    timeout=30,
                )
            if r2.status_code < 400 and r2.json().get("status") == "COMPLETED":
                status = "COMPLETED"
        if status == "COMPLETED":
            _update_order(order["order_id"], {"status": "paid"})
            order = _get_order(order["order_id"])
            return self._status_payload(order, "paid")
        return self._status_payload(order, "pending")

    def get_order(self, order_id):
        order = _get_order(order_id)
        if not order:
            return None
        return {
            "order_id": order["order_id"],
            "tenant_id": order["tenant_id"],
            "package": order["package"],
            "amount": order["amount"],
            "currency": order["currency"],
            "provider": order["provider"],
            "status": order["status"],
            "site_config": order.get("site_config", {}),
        }

    def _mark_tenant_paid(self, tenant_id, order_id):
        tenants_file = DATA_DIR / "tenants.json"
        tenants = []
        if tenants_file.exists():
            try:
                with open(tenants_file, "r", encoding="utf-8-sig") as f:
                    tenants = json.load(f)
            except Exception:
                tenants = []
        for t in tenants:
            if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id:
                t["payment_status"] = "paid"
                t["payment_order_id"] = order_id
                break
        with open(tenants_file, "w", encoding="utf-8-sig") as f:
            json.dump(tenants, f, indent=2, ensure_ascii=False)

    async def finalize(self, order_id):
        order = _get_order(order_id)
        if not order:
            return {"status": "error", "detail": "Orden no encontrada"}
        if order["status"] != "paid":
            return {"status": "error", "detail": "La orden no esta pagada"}
        if order.get("generated"):
            return {"status": "success", "generated": True, "preview_url": order.get("preview_url", ""), "order_id": order_id}

        from app.services.website_service import WebsiteService
        website_service = WebsiteService()
        cfg = order.get("site_config", {})
        try:
            result = await website_service.generate_modular_service(
                tenant_id=order["tenant_id"],
                industry=cfg.get("industry", ""),
                objective=cfg.get("objective", ""),
                audience=cfg.get("audience", ""),
                tone=cfg.get("tone", "amigable"),
                package=order["package"],
                brand_hex=cfg.get("brand_hex", "#2563eb"),
                brand_secondary=cfg.get("brand_secondary", "#764ba2"),
                visual_style=cfg.get("visual_style", "moderno"),
                page_type=cfg.get("page_type", "landing"),
                calendly_url=cfg.get("calendly_url", ""),
                contact_email=cfg.get("contact_email", ""),
                contact_phone=cfg.get("contact_phone", ""),
                contact_address=cfg.get("contact_address", ""),
            )
        except Exception as e:
            logger.error(f"Error en finalize generando sitio: {e}")
            return {"status": "error", "detail": f"Error generando el sitio: {e}"}
        if result.get("status") != "success":
            return {"status": "error", "detail": result.get("detail", "Error generando el sitio")}
        preview = result["preview_url"]
        _update_order(order_id, {"generated": True, "preview_url": preview})
        try:
            self._mark_tenant_paid(order["tenant_id"], order_id)
        except Exception as e:
            logger.warning(f"No se pudo marcar tenant como pagado: {e}")
        return {"status": "success", "generated": True, "preview_url": preview, "order_id": order_id}


payment_service = PaymentService()
