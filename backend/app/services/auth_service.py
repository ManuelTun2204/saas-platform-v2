import os
import json
import jwt
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production-" + secrets.token_hex(16))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()


class AuthService:
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            if not hashed_password or '$' not in hashed_password:
                return False
            salt, stored_hash = hashed_password.split('$', 1)
            hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hash_obj.hex() == stored_hash
        except Exception as e:
            logger.error(f"Error verificando password: {e}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.exceptions.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError, jwt.exceptions.PyJWTError):
            raise HTTPException(status_code=401, detail="Token inválido")
        except Exception as e:
            logger.error(f"Error decodificando token: {e}")
            raise HTTPException(status_code=401, detail="Token inválido")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
        token = credentials.credentials
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")
        username = payload.get("username") or payload.get("sub")
        
        # Verificar que el usuario siga existiendo y usar su rol actual
        # (los usuarios eliminados o con rol cambiado pierden/actualizan acceso de inmediato)
        try:
            users_file = DATA_DIR / "users.json"
            if not users_file.exists():
                raise HTTPException(status_code=401, detail="Usuario no encontrado")
            with open(users_file, 'r', encoding='utf-8-sig') as f:
                users = json.load(f)
            user = next((u for u in users if u.get("username") == username), None)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verificando usuario: {e}")
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        return {
            "user_id": username,
            "username": username,
            "role": user.get("role", "user")
        }


auth_service = AuthService()