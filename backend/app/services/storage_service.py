import json
import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Ruta base dentro de Docker: /app/data/storage
STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class StorageService:
    """Servicio de persistencia JSON con soporte UTF-8 BOM para Windows"""
    
    @staticmethod
    def _get_file_path(collection: str) -> Path:
        return STORAGE_DIR / f"{collection}.json"
    
    @staticmethod
    def _read_json(collection: str) -> List[Dict]:
        file_path = StorageService._get_file_path(collection)
        if not file_path.exists():
            return []
        
        try:
            # CRÍTICO: utf-8-sig para manejar BOM de Windows
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error leyendo {collection}: {e}")
            return []
    
    @staticmethod
    def _write_json(collection: str, data: List[Dict]):
        file_path = StorageService._get_file_path(collection)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = None
        try:
            # Escritura atómica: primero a un archivo temporal y luego se reemplaza,
            # evita archivos corruptos si dos workers escriben a la vez.
            fd, tmp_path = tempfile.mkstemp(dir=str(file_path.parent), prefix=f".{collection}.", suffix=".tmp")
            with os.fdopen(fd, 'w', encoding='utf-8-sig') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, file_path)
            tmp_path = None
        except IOError as e:
            logger.error(f"Error escribiendo {collection}: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
    
    # ===== TENANTS =====
    @staticmethod
    def get_all_tenants() -> List[Dict]:
        return StorageService._read_json("tenants")
    
    @staticmethod
    def get_tenant(tenant_id: str) -> Optional[Dict]:
        tenants = StorageService.get_all_tenants()
        return next((t for t in tenants if t.get("tenant_id") == tenant_id or t.get("id") == tenant_id), None)
    
    @staticmethod
    def create_tenant(tenant_data: Dict) -> Dict:
        tenants = StorageService.get_all_tenants()
        tenant_key = tenant_data.get("tenant_id", tenant_data.get("id"))
        if tenant_key and any(t.get("tenant_id") == tenant_key or t.get("id") == tenant_key for t in tenants):
            raise ValueError(f"Tenant {tenant_key} ya existe")
        tenants.append(tenant_data)
        StorageService._write_json("tenants", tenants)
        return tenant_data
    
    # ===== LEADS =====
    @staticmethod
    def get_all_leads() -> List[Dict]:
        return StorageService._read_json("leads")
    
    @staticmethod
    def get_leads_by_tenant(tenant_id: str) -> List[Dict]:
        leads = StorageService.get_all_leads()
        return [l for l in leads if l["tenant_id"] == tenant_id]
    
    @staticmethod
    def save_lead(lead_data: Dict) -> Dict:
        leads = StorageService.get_all_leads()
        # Evitar duplicados por email + tenant
        if any(l["tenant_id"] == lead_data["tenant_id"] and l["email"] == lead_data["email"] for l in leads):
            logger.info(f"Lead duplicado ignorado: {lead_data['email']}")
            return lead_data
        leads.append(lead_data)
        StorageService._write_json("leads", leads)
        return lead_data
    
    # ===== CONVERSATIONS =====
    @staticmethod
    def get_conversations_by_tenant(tenant_id: str) -> List[Dict]:
        conversations = StorageService._read_json("conversations")
        return [c for c in conversations if c["tenant_id"] == tenant_id]
    
    @staticmethod
    def save_conversation(conv_data: Dict) -> Dict:
        conversations = StorageService._read_json("conversations")
        conversations.append(conv_data)
        StorageService._write_json("conversations", conversations)
        return conv_data
    
    @staticmethod
    def get_all_conversations() -> List[Dict]:
        """Obtiene todas las conversaciones de todos los tenants"""
        return StorageService._read_json("conversations")