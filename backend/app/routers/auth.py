import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas import LoginRequest, RefreshRequest, RegisterRequest
from app.deps import DATA_DIR, auth_service, check_rate_limit, read_json_file, require_admin, write_json_atomic

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/auth/login")
async def login(request: LoginRequest, http_request: Request):
    """Login con JWT tokens (con limite de intentos para evitar fuerza bruta)"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    # Limite global por IP (evita probar muchos usuarios) y por usuario+IP (evita fuerza bruta).
    # Solo los intentos FALLIDOS cuentan para el limite por usuario, para no bloquear logins legitimos.
    if not check_rate_limit(f"loginip:{client_ip}", limit=20, window_seconds=300):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera 5 minutos.")
    if not check_rate_limit(f"loginuser:{request.username}:{client_ip}", limit=5, window_seconds=300, consume=False):
        raise HTTPException(status_code=429, detail="Demasiados intentos para este usuario. Espera 5 minutos.")
    try:
        users_file = DATA_DIR / "users.json"
        if not users_file.exists():
            raise HTTPException(status_code=500, detail="Archivo de usuarios no encontrado")
        users = read_json_file(users_file, [])

        user = next((u for u in users if u.get("username") == request.username), None)
        if not user:
            check_rate_limit(f"loginuser:{request.username}:{client_ip}", limit=5, window_seconds=300)
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not auth_service.verify_password(request.password, user.get("password_hash", "")):
            check_rate_limit(f"loginuser:{request.username}:{client_ip}", limit=5, window_seconds=300)
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        user_data = {
            "sub": user.get("username"),
            "username": user.get("username"),
            "role": user.get("role", "user")
        }
        access_token = auth_service.create_access_token(data=user_data)
        refresh_token = auth_service.create_refresh_token(data=user_data)

        logger.info(f"✅ Login exitoso: {request.username}")

        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/refresh")
async def refresh_token(request: RefreshRequest):
    """Refrescar access token usando refresh token"""
    try:
        payload = auth_service.decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")

        username = payload.get("username") or payload.get("sub")

        users = read_json_file(DATA_DIR / "users.json", [])
        user = next((u for u in users if u.get("username") == username), None)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        user_data = {
            "sub": user.get("username"),
            "username": user.get("username"),
            "role": user.get("role", "user")
        }
        access_token = auth_service.create_access_token(data=user_data)
        refresh_token = auth_service.create_refresh_token(data=user_data)

        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/auth/me")
async def get_current_user_info(user: dict = Depends(auth_service.get_current_user)):
    """Obtener información del usuario actual"""
    return {"status": "success", "user": user}


@router.post("/api/auth/register")
async def register(request: RegisterRequest, current_user: dict = Depends(require_admin)):
    """Registrar nuevo usuario (solo admins)"""
    try:
        users = read_json_file(DATA_DIR / "users.json", [])
        if any(u.get("username") == request.username for u in users):
            raise HTTPException(status_code=400, detail="Usuario ya existe")

        new_user = {
            "username": request.username,
            "password_hash": auth_service.hash_password(request.password),
            "role": request.role,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        write_json_atomic(DATA_DIR / "users.json", users)

        logger.info(f"✅ Usuario registrado: {request.username}")
        return {"status": "success", "message": f"Usuario {request.username} creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users")
async def list_users(current_user: dict = Depends(require_admin)):
    """Listar todos los usuarios (solo admins)"""
    try:
        users = read_json_file(DATA_DIR / "users.json", [])
        safe_users = [
            {
                "username": u.get("username"),
                "role": u.get("role", "user"),
                "created_at": u.get("created_at", "")
            }
            for u in users
        ]
        return {"status": "success", "users": safe_users}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/users")
async def create_user(request: RegisterRequest, current_user: dict = Depends(require_admin)):
    """Crear nuevo usuario (solo admins)"""
    try:
        if request.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Rol debe ser 'admin' o 'user'")

        users = read_json_file(DATA_DIR / "users.json", [])
        if any(u.get("username") == request.username for u in users):
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        new_user = {
            "username": request.username,
            "password_hash": auth_service.hash_password(request.password),
            "role": request.role,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        write_json_atomic(DATA_DIR / "users.json", users)

        logger.info(f"Usuario creado: {request.username} (rol: {request.role})")
        return {"status": "success", "message": f"Usuario {request.username} creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/users/{username}")
async def delete_user(username: str, current_user: dict = Depends(require_admin)):
    """Eliminar usuario (solo admins, no puede eliminarse a sí mismo)"""
    try:
        if username == current_user.get("username"):
            raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

        users = read_json_file(DATA_DIR / "users.json", [])
        if not users:
            raise HTTPException(status_code=404, detail="No hay usuarios")

        new_users = [u for u in users if u.get("username") != username]
        if len(new_users) == len(users):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        write_json_atomic(DATA_DIR / "users.json", new_users)

        logger.info(f"Usuario eliminado: {username}")
        return {"status": "success", "message": f"Usuario {username} eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
