import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DOMAINS_FILE = DATA_DIR / "storage" / "domains.json"
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")


def _read_domains() -> dict:
    if DOMAINS_FILE.exists():
        try:
            with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_domains(data: dict):
    DOMAINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DOMAINS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(DOMAINS_FILE)


class DomainService:

    def register_domain(self, tenant_id: str, domain: str) -> dict:
        domains = _read_domains()
        domain = domain.strip().lower()
        if not domain:
            return {"status": "error", "detail": "Dominio requerido"}
        for d, info in domains.items():
            if info.get("tenant_id") == tenant_id and d != domain:
                del domains[d]
        if domain in domains and domains[domain].get("tenant_id") != tenant_id:
            return {"status": "error", "detail": "Este dominio ya esta en uso por otro negocio"}
        domains[domain] = {
            "tenant_id": tenant_id,
            "registered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "verified": False,
            "ssl_pending": True,
        }
        _write_domains(domains)
        return {
            "status": "success",
            "domain": domain,
            "instructions": self._get_dns_instructions(domain, tenant_id),
        }

    def verify_domain(self, domain: str) -> dict:
        domains = _read_domains()
        domain = domain.strip().lower()
        if domain not in domains:
            return {"status": "error", "detail": "Dominio no registrado"}
        domains[domain]["verified"] = True
        domains[domain]["ssl_pending"] = False
        domains[domain]["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _write_domains(domains)
        return {"status": "success", "domain": domain, "verified": True}

    def get_domain_for_tenant(self, tenant_id: str) -> str:
        domains = _read_domains()
        for domain, info in domains.items():
            if info.get("tenant_id") == tenant_id and info.get("verified"):
                return domain
        return ""

    def get_tenant_for_domain(self, domain: str) -> str:
        domains = _read_domains()
        domain = domain.strip().lower()
        if domain in domains:
            return domains[domain].get("tenant_id", "")
        return ""

    def list_domains(self) -> list:
        domains = _read_domains()
        result = []
        for domain, info in domains.items():
            result.append({
                "domain": domain,
                "tenant_id": info.get("tenant_id", ""),
                "verified": info.get("verified", False),
                "ssl_pending": info.get("ssl_pending", True),
                "registered_at": info.get("registered_at", ""),
            })
        return result

    def _get_dns_instructions(self, domain: str, tenant_id: str) -> dict:
        return {
            "type": "CNAME",
            "host": domain,
            "value": "saas-platform.com",
            "instructions": [
                f"1. Ve al panel de DNS de tu dominio ({domain})",
                "2. Agrega un registro CNAME:",
                f"   Host: @ o {domain}",
                f"   Value: saas-platform.com",
                f"   TTL: 3600",
                "3. Espera 24-48 horas para que se propague",
                "4. Una vez verificado, tu sitio estara disponible en https://" + domain,
            ],
        }


domain_service = DomainService()
