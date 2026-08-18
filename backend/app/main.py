import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.deps import BASE_DIR, DATA_DIR
from app.routers import auth, tenants, payments, analytics, leads, blog

# Mostrar en consola los logs de la app (costos de IA, errores, etc.)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="SaaS Platform Pro API", version="1.0.0")

# CORS
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos y datos generados
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
(DATA_DIR / "websites").mkdir(exist_ok=True)
(DATA_DIR / "exports").mkdir(exist_ok=True)
app.mount("/data/websites", StaticFiles(directory=str(DATA_DIR / "websites")), name="websites")
app.mount("/data/exports", StaticFiles(directory=str(DATA_DIR / "exports")), name="exports")

# Routers
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(payments.router)
app.include_router(analytics.router)
app.include_router(leads.router)
app.include_router(blog.router)


@app.get("/")
async def serve_admin_panel():
    """Sirve el panel admin con headers anti-cache"""
    admin_file = BASE_DIR / "static" / "admin" / "index.html"
    if not admin_file.exists():
        raise HTTPException(status_code=404, detail="Panel no encontrado")

    content = admin_file.read_bytes().decode('utf-8')

    return HTMLResponse(
        content=content,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/landing")
async def serve_landing():
    """Landing pública con escaparate de plantillas y generador"""
    landing_file = BASE_DIR / "static" / "index.html"
    if not landing_file.exists():
        raise HTTPException(status_code=404, detail="Landing no encontrada")
    content = landing_file.read_bytes().decode('utf-8')
    return HTMLResponse(
        content=content,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
