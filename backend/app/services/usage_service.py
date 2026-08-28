"""
Servicio de uso (chat) por tenant: cuenta mensajes por mes y aplica
limites segun el plan/paquete del tenant, para evitar que un cliente
consuma API de OpenRouter sin control.
"""
import logging
from datetime import datetime

from app.deps import DATA_DIR, read_json_file, write_json_atomic

logger = logging.getLogger(__name__)

# Limite de mensajes de chat por plan (por mes). Si el tenant no tiene
# un paquete reconocido, se usa DEFAULT_CHAT_LIMIT.
PLAN_CHAT_LIMITS = {
    "basic": 500,
    "chat_only": 500,
    "pro": 3000,
    "premium": 10000,
    "full": 10000,
}
DEFAULT_CHAT_LIMIT = 3000

USAGE_FILE = DATA_DIR / "storage" / "usage.json"


def _month_key() -> str:
    return datetime.now().strftime("%Y-%m")


def current_usage(tenant_id: str) -> int:
    usage = read_json_file(USAGE_FILE, {})
    return usage.get(tenant_id, {}).get(_month_key(), 0)


def get_limit(package) -> int:
    if not package:
        return DEFAULT_CHAT_LIMIT
    key = str(package).strip().lower()
    return PLAN_CHAT_LIMITS.get(key, DEFAULT_CHAT_LIMIT)


def enforce_usage(tenant_id: str, package):
    """
    Verifica el limite de mensajes del mes. Si hay presupuesto, lo consume.

    Retorna (permitido, usado_tras_consumir, limite, restantes).
    """
    limit = get_limit(package)
    used = current_usage(tenant_id)
    if used >= limit:
        return False, used, limit, 0

    usage = read_json_file(USAGE_FILE, {})
    month = _month_key()
    tenant_usage = usage.get(tenant_id, {})
    tenant_usage[month] = tenant_usage.get(month, 0) + 1
    usage[tenant_id] = tenant_usage
    try:
        write_json_atomic(USAGE_FILE, usage)
    except Exception as e:
        logger.warning(f"No se pudo guardar el uso de chat: {e}")

    new_used = used + 1
    return True, new_used, limit, max(0, limit - new_used)
