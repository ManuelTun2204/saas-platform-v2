# LEEME-DEPLOY — Subir todo (incluida la demo) a un hosting

Guía práctica y paso a paso para llevar el **SaaS Platform v2 + la página demo de venta (`/demo`)** a internet en un servidor real.

> Si quieres el detalle técnico completo, complementa con `docs/INFO-TECNICA-Y-DEPLOY.md`.
> Este LEEME es lo que sigues en el momento de subirlo.

---

## 0. Qué vas a conseguir

| URL | Contenido |
|---|---|
| `https://tu-dominio.com/` | Panel admin (login `admin`/`admin123`) |
| `https://tu-dominio.com/demo` | ⭐ Página de venta para clientes (listo para compartir) |
| `https://tu-dominio.com/landing` | Landing pública del SaaS |

---

## 1. Elegir y contratar un VPS (recomendado)

El método más fiel a cómo lo pruebas hoy es un **VPS con Docker**.

| Proveedor | Aprox. precio | Nota |
|---|---|---|
| **Hetzner** / **Contabo** | ~€5–10/mes | Buen precio/calidad |
| **DigitalOcean** / **Vultr** / **Linode** | ~$10–12/mes | Muy usados, buena documentación |
| **Railway/Render** (PaaS) | varía | Más fácil pero requiere manejar la persistencia de `data/` |

**Requisitos mínimos del VPS:** 2 vCPU · 4 GB RAM · 40 GB SSD · Ubuntu 22.04/24.04.

---

## 2. Comprar el dominio y apuntarlo

1. Compra un dominio (Namecheap / GoDaddy / Porkbun / Cloudflare).
2. En el panel del registrar, crea un registro **A** que apunte a la **IP pública de tu VPS**:
   ```
   Nombre: @        → 1.2.3.4 (IP de tu VPS)
   Nombre: www      → 1.2.3.4 (IP de tu VPS)
   ```
3. Espera a que **propaguen** (minutos–horas). Verifica con:
   ```bash
   ping tu-dominio.com
   ```

---

## 3. Conectarte al servidor y prepararlo

Desde tu PC (PowerShell funciona):
```bash
ssh root@TU_IP_O_DOMINIO
```

Una vez dentro del servidor:
```bash
# Actualiza el sistema
apt update && apt upgrade -y

# Instala Git y Docker
apt install -y git curl
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

Verifica:
```bash
docker --version
docker compose version
```

---

## 4. Bajar el código del repositorio

En el servidor:
```bash
cd /opt
git clone https://github.com/ManuelTun2204/saas-platform-v2.git
cd saas-platform-v2
```

---

## 5. Crear el `.env` de producción

En el servidor, crea el archivo con tus claves reales (este `.env` NO se sube a git):
```bash
cp .env.example .env
nano .env
```

**Obligatorio dejar bien en producción:**

| Variable | Valor para producción |
|---|---|
| `OPENROUTER_API_KEY` | Tu clave real (sin ella no funciona la IA) |
| `JWT_SECRET_KEY` | Un secreto LARGO y aleatorio (muy importante) |
| `ADMIN_EMAIL` | Tu correo |
| `PUBLIC_URL` | `https://tu-dominio.com` ⚠️ |
| `ALLOWED_ORIGINS` | `https://tu-dominio.com` (NO `*`) |
| `RESEND_API_KEY` | Para que lleguen los emails de leads |
| `PRICE_BASIC/PRO/PREMIUM` | Tus precios (defaults 29/79/149 USD) |

> ⚠️ `PUBLIC_URL` y `ALLOWED_ORIGINS` deben usar el dominio **https** real, o los emails/embeds apuntarán a `localhost`.

Guarda (`Ctrl+O`, `Enter`, `Ctrl+X`).

> 🔐 El `.env` va en `/opt/saas-platform-v2/.env`. NUNCA lo subas a git. El repo ya tiene `.env` en `.gitignore`.

---

## 6. Construir y arrancar

En el servidor (dentro de `/opt/saas-platform-v2`):
```bash
docker compose up -d --build backend
```

- El **primer build** tarda varios minutos (descarga dependencias + hornea el modelo de IA).
- Verifica:
```bash
curl http://localhost:8000/health
```
Debe responder: `{"status":"ok"}`

Prueba ya la demo en el servidor:
```bash
curl -I http://localhost:8000/demo
```

---

## 7. Exponerlo por HTTPS con Nginx + SSL (certbot)

Instala Nginx y el certificado:
```bash
apt install -y nginx certbot python3-certbot-nginx
```

Crea `/etc/nginx/sites-available/saas`:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Actívalo y obtén el SSL automático:
```bash
ln -s /etc/nginx/sites-available/saas /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

> `certbot` edita solo la config para activar HTTPS y añade la renovación automática.

**Revisa que la demo cargue por HTTPS:**
```bash
curl -I https://tu-dominio.com/demo
```

---

## 8. Probar todo ya en producción

| URL | Esperas |
|---|---|
| `https://tu-dominio.com/` | Login admin |
| `https://tu-dominio.com/demo` | ⭐ Página demo con imágenes |
| `https://tu-dominio.com/landing` | Landing pública |
| `https://tu-dominio.com/health` | `{"status":"ok"}` |

**Comparte con clientes:**
- Página demo: `https://tu-dominio.com/demo`
- Video: `cliente-demo/video-demo-whatsapp.mp4` (envíalo por WhatsApp)

---

## 9. Mantenimiento (recuerda hacerlo)

Cada vez que hagas cambios en el repo (desde tu PC de trabajo):
```bash
cd /opt/saas-platform-v2
git pull
docker compose up -d --build backend
```

**Backups de los datos** (importante; `data/` guarda tenants, leads, pedidos, sitios):
```bash
cd /opt/saas-platform-v2
cp -r data backups/data-$(date +%F)
```
> Considera un cron diario o `rsync` a otro sitio.

---

## 10. Solución de problemas en producción

| Problema | Solución |
|---|---|
| Entra por HTTP pero no por HTTPS | Repasa el paso 7 (nginx + certbot) y que `PUBLIC_URL` use https |
| `JWT_SECRET_KEY` error | Falta la variable → pone un valor largo en `.env` (paso 5) |
| Las imágenes de la demo no cargan | La demo usa el volumen `./cliente-demo`; verifica que existe en `/opt/saas-platform-v2/cliente-demo` |
| No llegan los emails | Revisa `RESEND_API_KEY` y que `PUBLIC_URL` y `ADMIN_EMAIL` estén bien |
| El sitio del cliente no se ve | Mira `data/websites/` y regenera / vuelve a `docker compose up -d --build backend` |

---

*LEEME-DEPLOY · Para subir SaaS Platform v2 + demo a un VPS con Docker · agosto 2026*
