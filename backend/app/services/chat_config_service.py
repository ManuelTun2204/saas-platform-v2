import logging
from pathlib import Path
from typing import Dict

from app.deps import DATA_DIR, read_json_file, write_json_atomic

logger = logging.getLogger(__name__)

CHAT_CONFIGS_FILE = DATA_DIR / "storage" / "chat_configs.json"

QUICK_REPLY_LIMIT = 4
QUICK_REPLY_MAX_LEN = 60

DEFAULT_SUBTITLE = "En línea · responde al instante"
DEFAULT_WELCOME = "¡Hola! 👋 Soy el asistente virtual de la empresa. ¿En qué puedo ayudarte hoy?"
DEFAULT_QUICK_REPLIES = ["¿Qué servicios ofrecen?", "¿Cuál es su horario?", "Quiero que me contacten"]


def _tenant_company_name(tenant_id: str) -> str:
    try:
        tenants = read_json_file(DATA_DIR / "tenants.json", [])
        t = next((x for x in tenants if x.get("tenant_id") == tenant_id or x.get("id") == tenant_id), None)
        return (t or {}).get("company_name", "") or tenant_id
    except Exception as e:
        logger.warning(f"No se pudo leer nombre del tenant {tenant_id}: {e}")
        return tenant_id


def default_chat_config(tenant_id: str) -> Dict:
    """Configuracion por defecto del widget de chat para un tenant"""
    company = _tenant_company_name(tenant_id)
    is_real = company != tenant_id
    return {
        "title": f"Asistente de {company}" if is_real else "Asistente Virtual",
        "subtitle": DEFAULT_SUBTITLE,
        "primary_color": "#667eea",
        "secondary_color": "#764ba2",
        "avatar_url": "",
        "welcome": f"¡Hola! 👋 Soy el asistente virtual de {company}. ¿En qué puedo ayudarte?" if is_real else DEFAULT_WELCOME,
        "quick_replies": list(DEFAULT_QUICK_REPLIES),
    }


def _read_all_configs() -> Dict:
    try:
        data = read_json_file(CHAT_CONFIGS_FILE, {})
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"Error leyendo configs de chat: {e}")
        return {}


def _clean_config(data: Dict) -> Dict:
    """Valida y normaliza los campos guardados por el admin"""
    d = {
        "title": str(data.get("title", "")).strip()[:80],
        "subtitle": str(data.get("subtitle", "")).strip()[:120],
        "primary_color": str(data.get("primary_color", "")).strip()[:9],
        "secondary_color": str(data.get("secondary_color", "")).strip()[:9],
        "avatar_url": str(data.get("avatar_url", "")).strip()[:500],
        "welcome": str(data.get("welcome", "")).strip()[:400],
        "quick_replies": [],
    }
    qr = data.get("quick_replies", [])
    if isinstance(qr, str):
        qr = [x.strip() for x in qr.split(",") if x.strip()]
    for item in qr[:QUICK_REPLY_LIMIT]:
        if isinstance(item, str) and item.strip():
            d["quick_replies"].append(item.strip()[:QUICK_REPLY_MAX_LEN])
    if not d["quick_replies"]:
        d["quick_replies"] = list(DEFAULT_QUICK_REPLIES)
    return d


def get_chat_config(tenant_id: str) -> Dict:
    """Configuracion final: defaults + lo guardado por el admin"""
    config = default_chat_config(tenant_id)
    stored = _read_all_configs().get(tenant_id)
    if stored and isinstance(stored, dict):
        config.update(stored)
    return config


def save_chat_config(tenant_id: str, data: Dict) -> Dict:
    """Guarda la configuracion del widget para un tenant"""
    configs = _read_all_configs()
    configs[tenant_id] = _clean_config(data)
    write_json_atomic(CHAT_CONFIGS_FILE, configs)
    return configs[tenant_id]


def build_widget_snippet(tenant_id: str, public_url: str) -> str:
    """Codigo de instalacion de una sola linea para paginas existentes"""
    base = public_url.rstrip("/")
    return f'<script src="{base}/static/widget/widget.js" data-tenant="{tenant_id}"></script>'
