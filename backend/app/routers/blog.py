import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.deps import DATA_DIR, require_admin, read_json_file, write_json_atomic

logger = logging.getLogger(__name__)
router = APIRouter()

BLOG_DIR = DATA_DIR / "websites"


def _blog_dir(tenant_id: str) -> Path:
    d = BLOG_DIR / tenant_id / "blog"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _posts_file(tenant_id: str) -> Path:
    return _blog_dir(tenant_id) / "posts.json"


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def _render_markdown(text: str) -> str:
    """Renderizado basico de markdown a HTML."""
    text = re.sub(r'^### (.+)$', r'<h3 class="text-xl font-bold mt-6 mb-3">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2 class="text-2xl font-bold mt-8 mb-4">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1 class="text-3xl font-bold mt-10 mb-5">\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" class="text-blue-600 hover:underline">\1</a>', text)
    text = re.sub(r'^- (.+)$', r'<li class="ml-4">\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li[^>]*>.*</li>\n?)+', lambda m: f'<ul class="list-disc space-y-1 mb-4">{m.group(0)}</ul>', text)
    paragraphs = []
    for block in text.split('\n\n'):
        block = block.strip()
        if block and not block.startswith('<h') and not block.startswith('<ul'):
            paragraphs.append(f'<p class="mb-4 text-gray-700 leading-relaxed">{block}</p>')
        else:
            paragraphs.append(block)
    return '\n'.join(paragraphs)


@router.get("/api/blog/{tenant_id}")
async def list_posts(tenant_id: str):
    """Lista publicos los posts publicados (acceso publico)."""
    posts = read_json_file(_posts_file(tenant_id), [])
    published = [p for p in posts if p.get("published")]
    published.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return {"status": "success", "posts": published}


@router.get("/api/blog/{tenant_id}/all")
async def list_all_posts(tenant_id: str, current_user: dict = Depends(require_admin)):
    """Lista todos los posts (admin, incluye borradores)."""
    posts = read_json_file(_posts_file(tenant_id), [])
    posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return {"status": "success", "posts": posts}


@router.post("/api/blog/{tenant_id}")
async def create_post(tenant_id: str, data: dict, current_user: dict = Depends(require_admin)):
    """Crear un post del blog."""
    posts = read_json_file(_posts_file(tenant_id), [])
    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titulo requerido")

    slug = _slugify(title)
    existing_slugs = {p.get("slug") for p in posts}
    if slug in existing_slugs:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    post = {
        "id": uuid.uuid4().hex[:12],
        "title": title,
        "slug": slug,
        "excerpt": data.get("excerpt", "")[:200],
        "content": data.get("content", ""),
        "image": data.get("image", ""),
        "tags": data.get("tags", []),
        "published": data.get("published", False),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    posts.append(post)
    write_json_atomic(_posts_file(tenant_id), posts)
    return {"status": "success", "post": post}


@router.put("/api/blog/{tenant_id}/{post_id}")
async def update_post(tenant_id: str, post_id: str, data: dict, current_user: dict = Depends(require_admin)):
    """Actualizar un post."""
    posts = read_json_file(_posts_file(tenant_id), [])
    for p in posts:
        if p.get("id") == post_id:
            if "title" in data:
                p["title"] = data["title"]
            if "excerpt" in data:
                p["excerpt"] = data["excerpt"][:200]
            if "content" in data:
                p["content"] = data["content"]
            if "image" in data:
                p["image"] = data["image"]
            if "tags" in data:
                p["tags"] = data["tags"]
            if "published" in data:
                p["published"] = data["published"]
            p["updated_at"] = datetime.now().isoformat()
            write_json_atomic(_posts_file(tenant_id), posts)
            return {"status": "success", "post": p}
    raise HTTPException(status_code=404, detail="Post no encontrado")


@router.delete("/api/blog/{tenant_id}/{post_id}")
async def delete_post(tenant_id: str, post_id: str, current_user: dict = Depends(require_admin)):
    """Eliminar un post."""
    posts = read_json_file(_posts_file(tenant_id), [])
    posts = [p for p in posts if p.get("id") != post_id]
    write_json_atomic(_posts_file(tenant_id), posts)
    return {"status": "success"}


@router.get("/blog/{tenant_id}/{slug}", response_class=HTMLResponse)
async def view_post(tenant_id: str, slug: str):
    """Renderiza un post individual como pagina HTML completa."""
    posts = read_json_file(_posts_file(tenant_id), [])
    post = next((p for p in posts if p.get("slug") == slug and p.get("published")), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    site_data_file = BLOG_DIR / tenant_id / "site_data.json"
    site_data = read_json_file(site_data_file, {})
    brand_hex = site_data.get("brand_hex", "#2563eb")
    brand_secondary = site_data.get("brand_secondary", "#764ba2")
    company_name = site_data.get("company_name", tenant_id)

    content_html = _render_markdown(post.get("content", ""))
    tags_html = "".join(f'<span class="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full">{t}</span>' for t in post.get("tags", []))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{post['title']} | {company_name}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='{brand_hex}'/><text x='50' y='68' font-size='55' font-weight='bold' text-anchor='middle' fill='white' font-family='Arial,sans-serif'>{company_name[0]}</text></svg>">
<script>tailwind.config={{theme:{{extend:{{colors:{{brand:'{brand_hex}'}}}}}}}}}}</script>
<style>.gradient-text{{background:linear-gradient(135deg,{brand_hex},{brand_secondary});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}</style>
</head>
<body class="bg-gray-50 font-sans">
<nav class="bg-white/90 backdrop-blur-md shadow-sm sticky top-0 z-50">
<div class="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
<a href="/data/websites/{tenant_id}/index.html" class="text-xl font-bold gradient-text">{company_name}</a>
<a href="/data/websites/{tenant_id}/index.html" class="text-sm text-gray-500 hover:text-gray-800">← Volver al sitio</a>
</div>
</nav>
<article class="max-w-4xl mx-auto px-4 py-12">
<div class="mb-8">
<p class="text-sm text-gray-500 mb-2">{post.get('created_at', '')[:10]}</p>
<h1 class="text-4xl font-bold text-gray-900 mb-4">{post['title']}</h1>
{'<p class="text-gray-600 text-lg mb-4">' + post.get('excerpt', '') + '</p>' if post.get('excerpt') else ''}
{'<div class="flex gap-2 mb-6">' + tags_html + '</div>' if tags_html else ''}
</div>
{('<img src="' + post['image'] + '" class="w-full h-80 object-cover rounded-2xl mb-8 shadow-lg">') if post.get('image') else ''}
<div class="prose prose-lg max-w-none text-gray-800 leading-relaxed">
{content_html}
</div>
</article>
<footer class="bg-gray-900 text-gray-400 py-8 text-center text-sm">
<p>&copy; 2026 {company_name}. Todos los derechos reservados.</p>
</footer>
</body></html>"""
    return HTMLResponse(content=html)
