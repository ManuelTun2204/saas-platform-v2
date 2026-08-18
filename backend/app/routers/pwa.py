import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from app.deps import DATA_DIR, require_admin, read_json_file

logger = logging.getLogger(__name__)
router = APIRouter()

WEBSITES_DIR = DATA_DIR / "websites"


@router.get("/app/{tenant_id}/manifest.json")
async def manifest(tenant_id: str):
    site_data = read_json_file(WEBSITES_DIR / tenant_id / "site_data.json", {})
    brand_hex = site_data.get("brand_hex", "#2563eb")
    company_name = site_data.get("company_name", tenant_id)
    return JSONResponse({
        "name": company_name + " - Panel",
        "short_name": company_name[:12],
        "description": "Dashboard de " + company_name,
        "start_url": "/app/" + tenant_id,
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": brand_hex,
        "icons": [
            {"src": "/app/" + tenant_id + "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/app/" + tenant_id + "/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })


@router.get("/app/{tenant_id}/icon-192.png")
@router.get("/app/{tenant_id}/icon-512.png")
async def icon(tenant_id: str):
    site_data = read_json_file(WEBSITES_DIR / tenant_id / "site_data.json", {})
    brand_hex = site_data.get("brand_hex", "#2563eb")
    company_name = site_data.get("company_name", tenant_id)
    initial = company_name[0].upper() if company_name else "B"
    size = 192 if "192" in str(tenant_id) else 512
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
<rect width="{size}" height="{size}" rx="{size//4}" fill="{brand_hex}"/>
<text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="{size//2}" font-weight="bold" font-family="Arial,sans-serif">{initial}</text>
</svg>'''
    return HTMLResponse(content=svg, media_type="image/svg+xml")


@router.get("/app/{tenant_id}", response_class=HTMLResponse)
async def mobile_dashboard(tenant_id: str):
    site_data = read_json_file(WEBSITES_DIR / tenant_id / "site_data.json", {})
    brand_hex = site_data.get("brand_hex", "#2563eb")
    brand_secondary = site_data.get("brand_secondary", "#764ba2")
    company_name = site_data.get("company_name", tenant_id)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="{brand_hex}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="/app/{tenant_id}/manifest.json">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='{brand_hex}'/><text x='50' y='68' font-size='55' font-weight='bold' text-anchor='middle' fill='white' font-family='Arial,sans-serif'>{company_name[0]}</text></svg>">
<title>{company_name} - Panel</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script>tailwind.config={{theme:{{extend:{{colors:{{brand:'{brand_hex}'}}}}}}}}}}</script>
<style>
*{{-webkit-tap-highlight-color:transparent;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding-bottom:80px;}}
.tab-active{{color:{brand_hex};border-bottom:2px solid {brand_hex};}}
.card-enter{{animation:slideUp .3s ease;}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
</style>
</head>
<body class="bg-gray-50 min-h-screen">

<!-- LOGIN SCREEN -->
<div id="login-screen" class="min-h-screen flex items-center justify-center p-6" style="background:linear-gradient(135deg,{brand_hex},{brand_secondary});">
<div class="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-sm">
<div class="text-center mb-6">
<div class="w-16 h-16 rounded-2xl mx-auto mb-3 flex items-center justify-center text-white text-2xl font-bold" style="background:{brand_hex}">{company_name[0]}</div>
<h1 class="text-xl font-bold text-gray-900">{company_name}</h1>
<p class="text-sm text-gray-500 mt-1">Panel de control</p>
</div>
<input type="text" id="login-user" class="w-full p-3 border rounded-xl mb-3 text-sm" placeholder="Usuario" autocomplete="username">
<input type="password" id="login-pass" class="w-full p-3 border rounded-xl mb-4 text-sm" placeholder="Contrasena" autocomplete="current-password">
<button onclick="doLogin()" class="w-full py-3 rounded-xl text-white font-bold text-sm" style="background:{brand_hex}">Ingresar</button>
<p id="login-error" class="text-red-500 text-xs mt-3 text-center hidden"></p>
</div>
</div>

<!-- APP (hidden until logged in) -->
<div id="app-screen" class="hidden">

<!-- HEADER -->
<header class="sticky top-0 z-40 bg-white/90 backdrop-blur-md shadow-sm px-4 py-3">
<div class="flex justify-between items-center">
<div>
<h1 class="font-bold text-lg text-gray-900" id="app-title">{company_name}</h1>
<p class="text-xs text-gray-500">Panel de control</p>
</div>
<div class="flex gap-3">
<button onclick="refreshData()" class="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-gray-200"><i class="fa-solid fa-rotate text-sm"></i></button>
<button onclick="logout()" class="w-9 h-9 rounded-full bg-red-50 flex items-center justify-center text-red-500 hover:bg-red-100"><i class="fa-solid fa-right-from-bracket text-sm"></i></button>
</div>
</div>
</header>

<!-- TABS -->
<nav class="sticky top-[52px] z-30 bg-white border-b flex">
<button onclick="showTab('stats')" class="tab-btn tab-active flex-1 py-3 text-center text-xs font-semibold" data-tab="stats">
<i class="fa-solid fa-chart-line block text-lg mb-0.5"></i>Stats
</button>
<button onclick="showTab('leads')" class="tab-btn flex-1 py-3 text-center text-xs font-semibold text-gray-400" data-tab="leads">
<i class="fa-solid fa-users block text-lg mb-0.5"></i>Leads
</button>
<button onclick="showTab('orders')" class="tab-btn flex-1 py-3 text-center text-xs font-semibold text-gray-400" data-tab="orders">
<i class="fa-solid fa-bag-shopping block text-lg mb-0.5"></i>Pedidos
</button>
<button onclick="showTab('blog')" class="tab-btn flex-1 py-3 text-center text-xs font-semibold text-gray-400" data-tab="blog">
<i class="fa-solid fa-pen-nib block text-lg mb-0.5"></i>Blog
</button>
</nav>

<!-- STATS -->
<div id="tab-stats" class="p-4 space-y-4">
<div class="grid grid-cols-2 gap-3">
<div class="bg-white p-4 rounded-2xl shadow-sm border card-enter">
<p class="text-3xl font-bold text-gray-900" id="stat-leads">0</p>
<p class="text-xs text-gray-500 mt-1">Leads totales</p>
</div>
<div class="bg-white p-4 rounded-2xl shadow-sm border card-enter">
<p class="text-3xl font-bold text-gray-900" id="stat-orders">0</p>
<p class="text-xs text-gray-500 mt-1">Pedidos</p>
</div>
<div class="bg-white p-4 rounded-2xl shadow-sm border card-enter">
<p class="text-3xl font-bold text-green-600" id="stat-revenue">$0</p>
<p class="text-xs text-gray-500 mt-1">Ingresos</p>
</div>
<div class="bg-white p-4 rounded-2xl shadow-sm border card-enter">
<p class="text-3xl font-bold text-blue-600" id="stat-blog">0</p>
<p class="text-xs text-gray-500 mt-1">Articulos</p>
</div>
</div>
<div class="bg-white p-4 rounded-2xl shadow-sm border">
<h3 class="font-bold text-sm mb-3">Leads recientes</h3>
<div id="recent-leads" class="space-y-2"></div>
</div>
<div class="bg-white p-4 rounded-2xl shadow-sm border">
<h3 class="font-bold text-sm mb-3">Pedidos pendientes</h3>
<div id="recent-orders" class="space-y-2"></div>
</div>
</div>

<!-- LEADS -->
<div id="tab-leads" class="p-4 hidden space-y-3">
<div class="flex justify-between items-center mb-2">
<h3 class="font-bold">Todos los Leads</h3>
<span id="leads-count" class="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-500">0</span>
</div>
<div id="leads-list" class="space-y-2"></div>
</div>

<!-- ORDERS -->
<div id="tab-orders" class="p-4 hidden space-y-3">
<div class="flex justify-between items-center mb-2">
<h3 class="font-bold">Todos los Pedidos</h3>
<span id="orders-count" class="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-500">0</span>
</div>
<div id="orders-list" class="space-y-2"></div>
</div>

<!-- BLOG -->
<div id="tab-blog" class="p-4 hidden space-y-3">
<div class="flex justify-between items-center mb-2">
<h3 class="font-bold">Mis Articulos</h3>
<span id="blog-count" class="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-500">0</span>
</div>
<div id="blog-list" class="space-y-2"></div>
</div>
</div><!-- /app-screen -->

<script>
var TENANT = '{tenant_id}';
var TOKEN = localStorage.getItem('saas_token') || '';
var allLeads = [];
var allOrders = [];
var allPosts = [];

function authHeaders() {{
    return {{ 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json' }};
}}

async function apiFetch(url, opts) {{
    opts = opts || {{}};
    opts.headers = Object.assign({{}}, authHeaders(), opts.headers || {{}});
    return fetch(url, opts);
}}

async function doLogin() {{
    var user = document.getElementById('login-user').value.trim();
    var pass = document.getElementById('login-pass').value;
    var errEl = document.getElementById('login-error');
    if (!user || !pass) {{ errEl.textContent = 'Completa todos los campos'; errEl.classList.remove('hidden'); return; }}
    try {{
        var res = await fetch('/api/auth/login', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ username: user, password: pass }})
        }});
        var data = await res.json();
        if (data.access_token) {{
            TOKEN = data.access_token;
            localStorage.setItem('saas_token', TOKEN);
            document.getElementById('login-screen').classList.add('hidden');
            document.getElementById('app-screen').classList.remove('hidden');
            refreshData();
        }} else {{
            errEl.textContent = data.detail || 'Credenciales incorrectas';
            errEl.classList.remove('hidden');
        }}
    }} catch(e) {{
        errEl.textContent = 'Error de conexion';
        errEl.classList.remove('hidden');
    }}
}}

document.getElementById('login-pass').addEventListener('keydown', function(e) {{ if (e.key === 'Enter') doLogin(); }});
document.getElementById('login-user').addEventListener('keydown', function(e) {{ if (e.key === 'Enter') doLogin(); }});

// Check if already logged in
(function() {{
    if (TOKEN) {{
        fetch('/api/auth/me', {{ headers: {{ 'Authorization': 'Bearer ' + TOKEN }} }})
            .then(function(r) {{ if (r.ok) {{
                document.getElementById('login-screen').classList.add('hidden');
                document.getElementById('app-screen').classList.remove('hidden');
                refreshData();
            }} else {{ localStorage.removeItem('saas_token'); TOKEN = ''; }}}})
            .catch(function(){{}});
    }}
}})();

function showTab(tab) {{
    document.querySelectorAll('[id^="tab-"]').forEach(function(el) {{ el.classList.add('hidden'); }});
    document.getElementById('tab-' + tab).classList.remove('hidden');
    document.querySelectorAll('.tab-btn').forEach(function(b) {{
        b.classList.remove('tab-active');
        b.classList.add('text-gray-400');
    }});
    document.querySelector('[data-tab="'+tab+'"]').classList.add('tab-active');
    document.querySelector('[data-tab="'+tab+'"]').classList.remove('text-gray-400');
}}

function renderLeads(leads) {{
    var el = document.getElementById('leads-list');
    document.getElementById('leads-count').textContent = leads.length;
    document.getElementById('stat-leads').textContent = leads.length;
    document.getElementById('recent-leads').innerHTML = '';
    if (!leads.length) {{
        el.innerHTML = '<p class="text-gray-400 text-center py-8">No hay leads todavia</p>';
        document.getElementById('recent-leads').innerHTML = '<p class="text-gray-400 text-sm text-center">Sin leads recientes</p>';
        return;
    }}
    var recentHtml = '';
    for (var i = 0; i < Math.min(5, leads.length); i++) {{
        var l = leads[i];
        recentHtml += '<div class="flex items-center gap-3 py-2 border-b last:border-0">';
        recentHtml += '<div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm">' + (l.name||'?')[0].toUpperCase() + '</div>';
        recentHtml += '<div class="flex-1 min-w-0"><p class="text-sm font-semibold truncate">' + (l.name||'Sin nombre') + '</p><p class="text-xs text-gray-500 truncate">' + (l.email||'') + '</p></div>';
        recentHtml += '<span class="text-xs text-gray-400">' + (l.created_at||'').slice(5,10) + '</span>';
        recentHtml += '</div>';
    }}
    document.getElementById('recent-leads').innerHTML = recentHtml;
    var html = '';
    for (var j = 0; j < leads.length; j++) {{
        var l2 = leads[j];
        html += '<div class="bg-white p-4 rounded-xl shadow-sm border card-enter">';
        html += '<div class="flex items-center gap-3">';
        html += '<div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">' + (l2.name||'?')[0].toUpperCase() + '</div>';
        html += '<div class="flex-1 min-w-0">';
        html += '<p class="font-semibold">' + (l2.name||'Sin nombre') + '</p>';
        html += '<p class="text-xs text-gray-500">' + (l2.email||'') + ' ' + (l2.phone||'') + '</p>';
        html += '</div></div>';
        if (l2.message) html += '<p class="text-sm text-gray-600 mt-2 ml-13">' + l2.message + '</p>';
        html += '<p class="text-xs text-gray-400 mt-2">' + (l2.created_at||'') + '</p>';
        html += '</div>';
    }}
    el.innerHTML = html;
}}

function renderOrders(orders) {{
    var el = document.getElementById('orders-list');
    document.getElementById('orders-count').textContent = orders.length;
    document.getElementById('stat-orders').textContent = orders.length;
    var revenue = orders.reduce(function(s,o){{ return s + (o.payment_status==='paid'?o.total:0); }}, 0);
    document.getElementById('stat-revenue').textContent = '$' + revenue.toFixed(2);
    document.getElementById('recent-orders').innerHTML = '';
    if (!orders.length) {{
        el.innerHTML = '<p class="text-gray-400 text-center py-8">No hay pedidos todavia</p>';
        document.getElementById('recent-orders').innerHTML = '<p class="text-gray-400 text-sm text-center">Sin pedidos pendientes</p>';
        return;
    }}
    var sc = {{pending:'bg-yellow-100 text-yellow-800',confirmed:'bg-blue-100 text-blue-800',shipped:'bg-purple-100 text-purple-800',delivered:'bg-green-100 text-green-800',cancelled:'bg-red-100 text-red-800'}};
    var pending = orders.filter(function(o){{ return o.status==='pending'; }});
    var recentPendHtml = '';
    for (var p = 0; p < Math.min(5, pending.length); p++) {{
        var o2 = pending[p];
        recentPendHtml += '<div class="flex items-center justify-between py-2 border-b last:border-0">';
        recentPendHtml += '<div><p class="text-sm font-semibold">' + o2.id + '</p><p class="text-xs text-gray-500">' + (o2.customer_name||'') + '</p></div>';
        recentPendHtml += '<span class="font-bold text-sm">$' + o2.total.toFixed(2) + '</span>';
        recentPendHtml += '</div>';
    }}
    document.getElementById('recent-orders').innerHTML = recentPendHtml || '<p class="text-green-600 text-sm text-center">Todo al dia!</p>';
    var html = '';
    for (var i = 0; i < orders.length; i++) {{
        var o = orders[i];
        html += '<div class="bg-white p-4 rounded-xl shadow-sm border card-enter">';
        html += '<div class="flex justify-between items-start">';
        html += '<div><p class="font-mono font-bold text-sm">' + o.id + '</p><p class="text-sm text-gray-700">' + (o.customer_name||'') + '</p></div>';
        html += '<div class="text-right"><p class="font-bold">$' + o.total.toFixed(2) + '</p>';
        html += '<span class="text-xs px-2 py-0.5 rounded-full ' + (sc[o.status]||'bg-gray-100') + '">' + o.status + '</span></div>';
        html += '</div>';
        html += '<p class="text-xs text-gray-400 mt-2">' + o.items.length + ' producto(s) — ' + (o.created_at||'').slice(0,10) + '</p>';
        html += '</div>';
    }}
    el.innerHTML = html;
}}

function renderBlog(posts) {{
    var el = document.getElementById('blog-list');
    document.getElementById('blog-count').textContent = posts.length;
    document.getElementById('stat-blog').textContent = posts.length;
    if (!posts.length) {{
        el.innerHTML = '<p class="text-gray-400 text-center py-8">No hay articulos todavia</p>';
        return;
    }}
    var html = '';
    for (var i = 0; i < posts.length; i++) {{
        var p = posts[i];
        var badge = p.published ? '<span class="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full">Publicado</span>' : '<span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded-full">Borrador</span>';
        html += '<div class="bg-white p-4 rounded-xl shadow-sm border card-enter">';
        html += '<div class="flex justify-between items-start">';
        html += '<div class="flex-1 min-w-0"><p class="font-bold text-sm truncate">' + p.title + '</p>';
        html += '<p class="text-xs text-gray-500 truncate">' + (p.excerpt||'') + '</p></div>';
        html += '<div class="ml-3">' + badge + '</div>';
        html += '</div>';
        html += '<p class="text-xs text-gray-400 mt-2">' + (p.created_at||'').slice(0,10) + '</p>';
        html += '</div>';
    }}
    el.innerHTML = html;
}}

async function refreshData() {{
    try {{
        var resL = await apiFetch('/api/tenants/' + TENANT + '/leads');
        if (resL.ok) {{
            var dL = await resL.json();
            allLeads = dL.leads || dL.data || [];
            allLeads.sort(function(a,b){{ return (b.created_at||'').localeCompare(a.created_at||''); }});
            renderLeads(allLeads);
        }}
    }} catch(e) {{ console.error('Leads error:', e); }}

    try {{
        var resO = await apiFetch('/api/store/' + TENANT + '/orders');
        if (resO.ok) {{
            var dO = await resO.json();
            allOrders = dO.orders || [];
            renderOrders(allOrders);
        }}
    }} catch(e) {{ console.error('Orders error:', e); }}

    try {{
        var resB = await apiFetch('/api/blog/' + TENANT + '/all');
        if (resB.ok) {{
            var dB = await resB.json();
            allPosts = dB.posts || [];
            renderBlog(allPosts);
        }}
    }} catch(e) {{ console.error('Blog error:', e); }}
}}

function logout() {{
    localStorage.removeItem('saas_token');
    window.location.href = '/';
}}

// Auto-refresh every 60s
setInterval(refreshData, 60000);
refreshData();
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/api/tenants/{tenant_id}/leads")
async def get_tenant_leads(tenant_id: str, current_user: dict = Depends(require_admin)):
    leads_file = WEBSITES_DIR / tenant_id / "leads.json"
    leads = read_json_file(leads_file, [])
    leads.sort(key=lambda l: l.get("created_at", ""), reverse=True)
    return {"status": "success", "leads": leads}
