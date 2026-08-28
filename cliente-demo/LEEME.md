# LEEME — Levantar todo en la PC #2 (la que sincronizas con git)

Este archivo te guía para dejar funcionando el **SaaS Platform v2 + la página demo de venta** en tu otra PC (donde haces `git pull` a diario).

> ⚠️ Recuerda: estas instrucciones son para la PC **secundaria** (p. ej. casa / Emilio Tun). En la PC principal sueles estar con el panel + Docker ya corriendo.

---

## 1. Requisitos previos (solo la primera vez)

| Requisito | Cómo verificarlo |
|---|---|
| **Git** | `git --version` |
| **Docker Desktop** (arrancado) | Abrir Docker Desktop y esperar a que diga "Engine running" |
| **Python 3.11** (opcional, solo para scripts) | `python --version` |

Si no está Docker Desktop abierto: **ábrelo y espera a que el icono esté de color** antes de seguir.

---

## 2. Traer los cambios desde el repositorio

Abre una terminal y ve a la carpeta del proyecto:

```bash
cd C:\projects\saas-platform-v2
git pull
```

Esto baja todo lo nuevo, **incluido**:
- La ruta `/demo` (ya está en `backend/app/main.py`).
- El volumen de la demo (`docker-compose.yml`).
- La carpeta `cliente-demo/` (la página + capturas + videos).
- Los documentos en `docs/`.

---

## 3. Configurar el archivo `.env` (importante)

El `.env` **NO se sube a git** (contiene claves secretas). En esta PC hay dos casos:

### Caso A: ya tienes un `.env` de antes
```bash
docker compose up -d --build backend
```
Si arranca bien, salta al paso 4.

### Caso B: no tienes `.env` (o el paso A falló)
Cópialo manualmente desde la PC principal (es lo más simple porque ya tiene tus claves reales). Si no puedes, crea uno mínimo:

```bash
cp .env.example .env
```

**Y edita `.env`** (con el Bloc de notas) para poner al menos estas claves:

| Variable | Valor |
|---|---|
| `OPENROUTER_API_KEY` | Tu clave real de OpenRouter (sin ella NO genera sitios ni chatbot) |
| `JWT_SECRET_KEY` | Un texto largo y aleatorio (obligatorio; sin él el backend no arranca) |
| `ADMIN_EMAIL` | Tu correo (recibe alertas de leads) |
| `PUBLIC_URL` | `http://localhost:8000` (local) — o tu dominio si ya está en hosting |
| `ALLOWED_ORIGINS` | `*` para pruebas locales |

> Consejo: si `JWT_SECRET_KEY` la pones distinta a la de la otra PC, **los usuarios/tokens no se compartirán entre PC** (cada una tiene su propia contraseña de admin local). Para el administrador no es problema: el admin se crea con `admin`/`admin123` en ambas.

---

## 4. Levantar el backend

```bash
docker compose up -d --build backend
```

- El **primer build** tarda varios minutos (descarga e instala dependencias + hornea el modelo de IA).
- Las veces siguientes son más rápidas.
- Si el comando "sale en rojo" pero al final dice que se construyó/inició, **es solo un aviso de PowerShell, no un error real**.

---

## 5. Verificar que todo funciona

Abre el navegador y revisa:

| Qué | URL | Resultado esperado |
|---|---|---|
| **Estado del servidor** | `http://localhost:8000/health` | Muestra `{"status":"ok"}` |
| **Panel admin** | `http://localhost:8000/` | Página de login (usa `admin` / `admin123`) |
| **⭐ Página demo de venta** | `http://localhost:8000/demo` | La página del restaurante con imágenes |
| **Landing del SaaS** | `http://localhost:8000/landing` | La página de presentación del producto |

Consejo rápido desde la terminal:
```bash
curl http://localhost:8000/health
```

---

## 6. Solución de problemas

| Problema | Causa / Solución |
|---|---|
| `http://localhost:8000/demo` no carga | ¿Docker arrancó? ¿Corriste `docker compose up`? Revísalo con `curl http://localhost:8000/health` |
| El backend no arranca y habla de `JWT_SECRET_KEY` | Faltan claves en `.env` → mira el punto 3, Caso B |
| El build "sale en rojo" | Aviso de PowerShell, no error. Comprueba con `/health` |
| Cambié un `.py` y no se ve | Reconstruye: `docker compose up -d --build backend` |
| Cambié `demo.html` o las capturas y no se ve | **No hace falta rebuild**: recarga el navegador con `Ctrl+Shift+R` (la carpeta está montada como volumen) |

---

## 7. Recordatorios del día a día

- **Para traer lo nuevo**: solo `git pull` y si hubo cambios en código (`.py`): `docker compose up -d --build backend`.
- **Para apagar**: `docker compose down`.
- **La demo se actualiza sola** al editar `cliente-demo/` (no requiere rebuild).
- **Los videos** (`cliente-demo/*.mp4`) pesan ~23 MB en total; se bajan con el `git pull`. Si quieres que no se sincronicen (para no ocupar espacio/tiempo), dímelo y los movemos a un lugar fuera del repo.

---

*LEEME generado para la PC #2 · Proyecto SaaS Platform v2 · agosto 2026*
