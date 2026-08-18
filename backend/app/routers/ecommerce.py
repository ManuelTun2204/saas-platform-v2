import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.deps import DATA_DIR, require_admin, read_json_file, write_json_atomic

logger = logging.getLogger(__name__)
router = APIRouter()

WEBSITES_DIR = DATA_DIR / "websites"
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")


def _store_dir(tenant_id: str) -> Path:
    d = WEBSITES_DIR / tenant_id / "store"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _products_file(tenant_id: str) -> Path:
    return _store_dir(tenant_id) / "products.json"


def _orders_file(tenant_id: str) -> Path:
    return _store_dir(tenant_id) / "orders.json"


def _config_file(tenant_id: str) -> Path:
    return _store_dir(tenant_id) / "config.json"


# ── Products CRUD ────────────────────────────────────────


@router.get("/api/store/{tenant_id}/products")
async def list_products(tenant_id: str):
    products = read_json_file(_products_file(tenant_id), [])
    active = [p for p in products if p.get("active", True)]
    active.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return {"status": "success", "products": active}


@router.get("/api/store/{tenant_id}/products/all")
async def list_all_products(tenant_id: str, current_user: dict = Depends(require_admin)):
    products = read_json_file(_products_file(tenant_id), [])
    products.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return {"status": "success", "products": products}


@router.post("/api/store/{tenant_id}/products")
async def create_product(tenant_id: str, data: dict, current_user: dict = Depends(require_admin)):
    products = read_json_file(_products_file(tenant_id), [])
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre del producto requerido")
    if not data.get("price") or float(data["price"]) <= 0:
        raise HTTPException(status_code=400, detail="Precio invalido")

    product = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "description": data.get("description", ""),
        "price": float(data["price"]),
        "compare_price": float(data.get("compare_price", 0) or 0),
        "image": data.get("image", ""),
        "category": data.get("category", ""),
        "stock": int(data.get("stock", 999)),
        "active": data.get("active", True),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    products.append(product)
    write_json_atomic(_products_file(tenant_id), products)
    return {"status": "success", "product": product}


@router.put("/api/store/{tenant_id}/products/{product_id}")
async def update_product(tenant_id: str, product_id: str, data: dict, current_user: dict = Depends(require_admin)):
    products = read_json_file(_products_file(tenant_id), [])
    for p in products:
        if p.get("id") == product_id:
            for key in ("name", "description", "price", "compare_price", "image", "category", "stock", "active"):
                if key in data:
                    p[key] = data[key]
            if "price" in data:
                p["price"] = float(data["price"])
            if "compare_price" in data:
                p["compare_price"] = float(data.get("compare_price", 0) or 0)
            if "stock" in data:
                p["stock"] = int(data["stock"])
            p["updated_at"] = datetime.now().isoformat()
            write_json_atomic(_products_file(tenant_id), products)
            return {"status": "success", "product": p}
    raise HTTPException(status_code=404, detail="Producto no encontrado")


@router.delete("/api/store/{tenant_id}/products/{product_id}")
async def delete_product(tenant_id: str, product_id: str, current_user: dict = Depends(require_admin)):
    products = read_json_file(_products_file(tenant_id), [])
    products = [p for p in products if p.get("id") != product_id]
    write_json_atomic(_products_file(tenant_id), products)
    return {"status": "success"}


# ── Store Config ─────────────────────────────────────────


@router.get("/api/store/{tenant_id}/config")
async def get_store_config(tenant_id: str):
    config = read_json_file(_config_file(tenant_id), {
        "currency": "USD",
        "currency_symbol": "$",
        "accept_mp": True,
        "accept_stripe": True,
        "accept_paypal": True,
        "whatsapp_number": "",
        "free_shipping_threshold": 0,
    })
    return {"status": "success", "config": config}


@router.post("/api/store/{tenant_id}/config")
async def save_store_config(tenant_id: str, data: dict, current_user: dict = Depends(require_admin)):
    write_json_atomic(_config_file(tenant_id), data)
    return {"status": "success"}


# ── Orders ───────────────────────────────────────────────


@router.get("/api/store/{tenant_id}/orders")
async def list_orders(tenant_id: str, current_user: dict = Depends(require_admin)):
    orders = read_json_file(_orders_file(tenant_id), [])
    orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return {"status": "success", "orders": orders}


@router.post("/api/store/{tenant_id}/orders")
async def create_order(tenant_id: str, data: dict):
    items = data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Carrito vacio")

    products = read_json_file(_products_file(tenant_id), [])
    product_map = {p["id"]: p for p in products}

    total = 0
    validated_items = []
    for item in items:
        pid = item.get("product_id")
        qty = int(item.get("quantity", 1))
        if pid not in product_map:
            raise HTTPException(status_code=400, detail=f"Producto {pid} no encontrado")
        p = product_map[pid]
        if not p.get("active", True):
            raise HTTPException(status_code=400, detail=f"Producto {p['name']} no disponible")
        subtotal = p["price"] * qty
        total += subtotal
        validated_items.append({
            "product_id": pid,
            "name": p["name"],
            "price": p["price"],
            "quantity": qty,
            "subtotal": subtotal,
            "image": p.get("image", ""),
        })

    order = {
        "id": "ORD-" + uuid.uuid4().hex[:8].upper(),
        "items": validated_items,
        "total": round(total, 2),
        "currency": "USD",
        "customer_name": data.get("customer_name", ""),
        "customer_email": data.get("customer_email", ""),
        "customer_phone": data.get("customer_phone", ""),
        "customer_address": data.get("customer_address", ""),
        "payment_method": data.get("payment_method", "demo"),
        "payment_status": "pending",
        "status": "pending",
        "notes": data.get("notes", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    orders = read_json_file(_orders_file(tenant_id), [])
    orders.append(order)
    write_json_atomic(_orders_file(tenant_id), orders)
    return {"status": "success", "order": order}


@router.put("/api/store/{tenant_id}/orders/{order_id}")
async def update_order(tenant_id: str, order_id: str, data: dict, current_user: dict = Depends(require_admin)):
    orders = read_json_file(_orders_file(tenant_id), [])
    for o in orders:
        if o.get("id") == order_id:
            if "status" in data:
                o["status"] = data["status"]
            if "payment_status" in data:
                o["payment_status"] = data["payment_status"]
            if "notes" in data:
                o["notes"] = data["notes"]
            o["updated_at"] = datetime.now().isoformat()
            write_json_atomic(_orders_file(tenant_id), orders)
            return {"status": "success", "order": o}
    raise HTTPException(status_code=404, detail="Orden no encontrada")


@router.delete("/api/store/{tenant_id}/orders/{order_id}")
async def delete_order(tenant_id: str, order_id: str, current_user: dict = Depends(require_admin)):
    orders = read_json_file(_orders_file(tenant_id), [])
    orders = [o for o in orders if o.get("id") != order_id]
    write_json_atomic(_orders_file(tenant_id), orders)
    return {"status": "success"}


# ── Storefront Page ──────────────────────────────────────


@router.get("/store/{tenant_id}", response_class=HTMLResponse)
async def store_page(tenant_id: str):
    site_data = read_json_file(WEBSITES_DIR / tenant_id / "site_data.json", {})
    config = read_json_file(_config_file(tenant_id), {
        "currency": "USD",
        "currency_symbol": "$",
        "whatsapp_number": "",
    })
    brand_hex = site_data.get("brand_hex", "#2563eb")
    brand_secondary = site_data.get("brand_secondary", "#764ba2")
    company_name = site_data.get("company_name", tenant_id)
    cs = config.get("currency_symbol", "$")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tienda en Linea | {company_name}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='{brand_hex}'/><text x='50' y='68' font-size='55' font-weight='bold' text-anchor='middle' fill='white' font-family='Arial,sans-serif'>{company_name[0]}</text></svg>">
<script>tailwind.config={{theme:{{extend:{{colors:{{brand:'{brand_hex}'}}}}}}}}}}</script>
<style>
.cart-badge{{position:absolute;top:-6px;right:-6px;background:#ef4444;color:#fff;border-radius:50%;width:20px;height:20px;font-size:11px;display:flex;align-items:center;justify-content:center;font-weight:bold;}}
.toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#10b981;color:#fff;padding:12px 24px;border-radius:12px;font-weight:600;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;}}
.toast.show{{opacity:1;}}
</style>
</head>
<body class="bg-gray-50 min-h-screen">

<!-- NAV -->
<nav class="bg-white/90 backdrop-blur-md shadow-sm sticky top-0 z-50">
<div class="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
<a href="/data/websites/{tenant_id}/index.html" class="text-xl font-bold" style="color:{brand_hex}">{company_name}</a>
<div class="flex items-center gap-4">
<a href="/data/websites/{tenant_id}/index.html" class="text-sm text-gray-500 hover:text-gray-800">Sitio Principal</a>
<button onclick="toggleCart()" class="relative text-gray-700 hover:text-gray-900 text-xl">
<i class="fa-solid fa-shopping-cart"></i>
<span id="cart-count" class="cart-badge hidden">0</span>
</button>
</div>
</div>
</nav>

<!-- HERO TIENDA -->
<div class="py-12 text-center" style="background:linear-gradient(135deg,{brand_hex}11,{brand_secondary}11)">
<h1 class="text-4xl font-bold text-gray-900 mb-3">Nuestra Tienda</h1>
<p class="text-gray-600 max-w-xl mx-auto">Explora nuestros productos y recibe en la puerta de tu casa.</p>
</div>

<!-- CATEGORIAS -->
<div id="categories-bar" class="max-w-6xl mx-auto px-4 py-4 flex gap-2 overflow-x-auto"></div>

<!-- PRODUCTS GRID -->
<main class="max-w-6xl mx-auto px-4 py-8">
<div id="products-grid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"></div>
<div id="no-products" class="hidden text-center py-16 text-gray-400">
<i class="fa-solid fa-box-open text-5xl mb-4"></i>
<p class="text-lg">No hay productos todavia</p>
</div>
</main>

<!-- CARRITO SIDEBAR -->
<div id="cart-overlay" class="hidden fixed inset-0 bg-black/40 z-50" onclick="toggleCart()"></div>
<div id="cart-sidebar" class="fixed top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl z-50 transform translate-x-full transition-transform duration-300">
<div class="flex flex-col h-full">
<div class="flex justify-between items-center p-5 border-b">
<h2 class="text-xl font-bold">Tu Carrito</h2>
<button onclick="toggleCart()" class="text-gray-500 hover:text-gray-800 text-2xl">&times;</button>
</div>
<div id="cart-items" class="flex-1 overflow-y-auto p-5 space-y-4"></div>
<div id="cart-empty" class="flex-1 flex items-center justify-center text-gray-400">
<div class="text-center"><i class="fa-solid fa-cart-shopping text-5xl mb-3"></i><p>Tu carrito esta vacio</p></div>
</div>
<div id="cart-footer" class="border-t p-5 space-y-3 hidden">
<div class="flex justify-between font-bold text-lg"><span>Total:</span><span id="cart-total">{cs}0.00</span></div>
<button onclick="openCheckout()" class="w-full py-3 rounded-xl text-white font-bold text-lg" style="background:{brand_hex}">Ir a Pagar</button>
</div>
</div>
</div>

<!-- CHECKOUT MODAL -->
<div id="checkout-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
<div class="bg-white rounded-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
<div class="flex justify-between items-center mb-5">
<h3 class="text-xl font-bold">Finalizar Compra</h3>
<button onclick="closeCheckout()" class="text-gray-500 hover:text-gray-800 text-2xl">&times;</button>
</div>
<div id="checkout-items" class="space-y-2 mb-4 text-sm"></div>
<div class="border-t pt-4 space-y-3">
<div><label class="block text-sm font-semibold mb-1">Nombre completo</label><input id="ck-name" class="w-full p-3 border rounded-lg" placeholder="Juan Perez"></div>
<div><label class="block text-sm font-semibold mb-1">Email</label><input id="ck-email" type="email" class="w-full p-3 border rounded-lg" placeholder="juan@email.com"></div>
<div><label class="block text-sm font-semibold mb-1">Telefono</label><input id="ck-phone" class="w-full p-3 border rounded-lg" placeholder="999-123-4567"></div>
<div><label class="block text-sm font-semibold mb-1">Direccion de envio</label><textarea id="ck-address" rows="2" class="w-full p-3 border rounded-lg" placeholder="Calle, numero, colonia, ciudad"></textarea></div>
<div><label class="block text-sm font-semibold mb-1">Notas (opcional)</label><textarea id="ck-notes" rows="2" class="w-full p-3 border rounded-lg" placeholder="Instrucciones especiales..."></textarea></div>
<div>
<label class="block text-sm font-semibold mb-2">Metodo de Pago</label>
<div class="grid grid-cols-3 gap-2">
<label class="border-2 rounded-lg p-3 text-center cursor-pointer hover:border-green-500 has-[:checked]:border-green-500 has-[:checked]:bg-green-50">
<input type="radio" name="pay-method" value="demo" class="hidden" checked>
<i class="fa-solid fa-cube text-green-600 text-xl"></i><p class="text-xs font-semibold mt-1">Demo</p>
</label>
<label class="border-2 rounded-lg p-3 text-center cursor-pointer hover:border-blue-500 has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50">
<input type="radio" name="pay-method" value="stripe" class="hidden">
<i class="fa-brands fa-stripe text-blue-600 text-xl"></i><p class="text-xs font-semibold mt-1">Stripe</p>
</label>
<label class="border-2 rounded-lg p-3 text-center cursor-pointer hover:border-sky-500 has-[:checked]:border-sky-500 has-[:checked]:bg-sky-50">
<input type="radio" name="pay-method" value="mercadopago" class="hidden">
<i class="fa-solid fa-b text-sky-600 text-xl"></i><p class="text-xs font-semibold mt-1">MP</p>
</label>
</div>
</div>
<div class="flex justify-between font-bold text-lg border-t pt-3 mt-3">
<span>Total:</span><span id="ck-total">{cs}0.00</span>
</div>
<div id="checkout-status" class="text-sm"></div>
<button onclick="placeOrder()" class="w-full py-3 rounded-xl bg-gray-900 text-white font-bold text-lg hover:bg-gray-800">Confirmar Pedido</button>
</div>
</div>
</div>

<!-- ORDER CONFIRMED -->
<div id="order-confirmed" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
<div class="bg-white rounded-2xl w-full max-w-md p-8 text-center">
<div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-check text-green-600 text-4xl"></i></div>
<h3 class="text-2xl font-bold mb-2">Pedido Recibido!</h3>
<p class="text-gray-600 mb-1">Tu numero de pedido es:</p>
<p id="confirmed-order-id" class="text-xl font-mono font-bold mb-4"></p>
<p class="text-sm text-gray-500 mb-6">Recibiras un email de confirmacion con los detalles de tu pedido.</p>
<button onclick="closeOrderConfirmed()" class="px-8 py-3 rounded-xl text-white font-bold" style="background:{brand_hex}">Seguir Comprando</button>
</div>
</div>

<!-- TOAST -->
<div id="toast" class="toast"></div>

<script>
var CART = [];
var ALL_PRODUCTS = [];
var CS = '{cs}';
var TENANT = '{tenant_id}';

function showToast(msg) {{
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function(){{ t.classList.remove('show'); }}, 2000);
}}

function toggleCart() {{
    var sidebar = document.getElementById('cart-sidebar');
    var overlay = document.getElementById('cart-overlay');
    var isOpen = !sidebar.classList.contains('translate-x-full');
    if (isOpen) {{
        sidebar.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }} else {{
        sidebar.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
    }}
}}

function addToCart(productId) {{
    var p = ALL_PRODUCTS.find(function(x){{ return x.id === productId; }});
    if (!p) return;
    var existing = CART.find(function(x){{ return x.product_id === productId; }});
    if (existing) {{
        existing.quantity++;
    }} else {{
        CART.push({{ product_id: p.id, name: p.name, price: p.price, image: p.image || '', quantity: 1 }});
    }}
    renderCart();
    showToast('Agregado: ' + p.name);
}}

function removeFromCart(productId) {{
    CART = CART.filter(function(x){{ return x.product_id !== productId; }});
    renderCart();
}}

function changeQty(productId, delta) {{
    var item = CART.find(function(x){{ return x.product_id === productId; }});
    if (!item) return;
    item.quantity += delta;
    if (item.quantity <= 0) {{
        CART = CART.filter(function(x){{ return x.product_id !== productId; }});
    }}
    renderCart();
}}

function renderCart() {{
    var countEl = document.getElementById('cart-count');
    var itemsEl = document.getElementById('cart-items');
    var emptyEl = document.getElementById('cart-empty');
    var footerEl = document.getElementById('cart-footer');
    var totalEl = document.getElementById('cart-total');
    var total = 0;
    var count = 0;
    var html = '';
    for (var i = 0; i < CART.length; i++) {{
        var it = CART[i];
        var sub = it.price * it.quantity;
        total += sub;
        count += it.quantity;
        html += '<div class="flex items-center gap-3 bg-gray-50 rounded-xl p-3">';
        if (it.image) html += '<img src="'+it.image+'" class="w-14 h-14 rounded-lg object-cover">';
        html += '<div class="flex-1 min-w-0">';
        html += '<p class="font-semibold text-sm truncate">'+it.name+'</p>';
        html += '<p class="text-sm text-gray-500">'+CS+it.price.toFixed(2)+'</p>';
        html += '</div>';
        html += '<div class="flex items-center gap-2">';
        html += '<button onclick="changeQty(\\''+it.product_id+'\\',-1)" class="w-7 h-7 rounded-full bg-gray-200 hover:bg-gray-300 text-sm">-</button>';
        html += '<span class="w-6 text-center font-semibold">'+it.quantity+'</span>';
        html += '<button onclick="changeQty(\\''+it.product_id+'\\',1)" class="w-7 h-7 rounded-full bg-gray-200 hover:bg-gray-300 text-sm">+</button>';
        html += '</div>';
        html += '<button onclick="removeFromCart(\\''+it.product_id+'\\')" class="text-red-400 hover:text-red-600 px-1"><i class="fa-solid fa-xmark"></i></button>';
        html += '</div>';
    }}
    countEl.textContent = count;
    countEl.classList.toggle('hidden', count === 0);
    if (CART.length === 0) {{
        itemsEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        footerEl.classList.add('hidden');
    }} else {{
        itemsEl.innerHTML = html;
        itemsEl.classList.remove('hidden');
        emptyEl.classList.add('hidden');
        footerEl.classList.remove('hidden');
        totalEl.textContent = CS + total.toFixed(2);
    }}
}}

function openCheckout() {{
    toggleCart();
    var items = CART;
    var total = 0;
    var html = '';
    for (var i = 0; i < items.length; i++) {{
        var sub = items[i].price * items[i].quantity;
        total += sub;
        html += '<div class="flex justify-between"><span>'+items[i].name+' x'+items[i].quantity+'</span><span>'+CS+sub.toFixed(2)+'</span></div>';
    }}
    document.getElementById('checkout-items').innerHTML = html;
    document.getElementById('ck-total').textContent = CS + total.toFixed(2);
    document.getElementById('checkout-modal').classList.remove('hidden');
}}

function closeCheckout() {{
    document.getElementById('checkout-modal').classList.add('hidden');
}}

async function placeOrder() {{
    var statusEl = document.getElementById('checkout-status');
    var name = document.getElementById('ck-name').value.trim();
    var email = document.getElementById('ck-email').value.trim();
    if (!name || !email) {{
        statusEl.innerHTML = '<span class="text-red-600">Nombre y email son obligatorios</span>';
        return;
    }}
    var payMethod = document.querySelector('input[name="pay-method"]:checked').value;
    statusEl.innerHTML = '<span class="text-blue-600">Procesando pedido...</span>';

    var payload = {{
        items: CART.map(function(c) {{ return {{ product_id: c.product_id, quantity: c.quantity }}; }}),
        customer_name: name,
        customer_email: email,
        customer_phone: document.getElementById('ck-phone').value,
        customer_address: document.getElementById('ck-address').value,
        notes: document.getElementById('ck-notes').value,
        payment_method: payMethod
    }};

    try {{
        var res = await fetch('/api/store/' + TENANT + '/orders', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
        }});
        var data = await res.json();
        if (data.status === 'success') {{
            CART = [];
            renderCart();
            closeCheckout();
            document.getElementById('confirmed-order-id').textContent = data.order.id;
            document.getElementById('order-confirmed').classList.remove('hidden');
        }} else {{
            statusEl.innerHTML = '<span class="text-red-600">' + (data.detail || 'Error') + '</span>';
        }}
    }} catch(e) {{
        statusEl.innerHTML = '<span class="text-red-600">' + e.message + '</span>';
    }}
}}

function closeOrderConfirmed() {{
    document.getElementById('order-confirmed').classList.add('hidden');
}}

function filterCategory(cat) {{
    var cards = document.querySelectorAll('.product-card');
    var btns = document.querySelectorAll('.cat-btn');
    btns.forEach(function(b){{ b.classList.remove('bg-gray-900','text-white'); b.classList.add('bg-gray-100'); }});
    event.target.classList.remove('bg-gray-100');
    event.target.classList.add('bg-gray-900','text-white');
    cards.forEach(function(c) {{
        if (!cat || c.dataset.cat === cat) c.style.display = '';
        else c.style.display = 'none';
    }});
}}

async function loadProducts() {{
    try {{
        var res = await fetch('/api/store/' + TENANT + '/products');
        var data = await res.json();
        if (data.status === 'success') {{
            ALL_PRODUCTS = data.products;
            renderProducts(data.products);
            renderCategories(data.products);
        }}
    }} catch(e) {{ console.error(e); }}
}}

function renderProducts(products) {{
    var grid = document.getElementById('products-grid');
    var noEl = document.getElementById('no-products');
    if (!products.length) {{
        grid.classList.add('hidden');
        noEl.classList.remove('hidden');
        return;
    }}
    grid.classList.remove('hidden');
    noEl.classList.add('hidden');
    var html = '';
    for (var i = 0; i < products.length; i++) {{
        var p = products[i];
        var hasDiscount = p.compare_price && p.compare_price > p.price;
        html += '<div class="product-card bg-white rounded-2xl shadow-sm border overflow-hidden hover:shadow-lg transition-all duration-300" data-cat="'+(p.category||'')+'">';
        if (p.image) html += '<img src="'+p.image+'" class="w-full h-48 object-cover">';
        else html += '<div class="w-full h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center"><i class="fa-solid fa-image text-gray-300 text-4xl"></i></div>';
        html += '<div class="p-4">';
        if (p.category) html += '<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 mb-2 inline-block">'+p.category+'</span>';
        html += '<h3 class="font-bold text-gray-900 mb-1 line-clamp-2">'+p.name+'</h3>';
        html += '<p class="text-sm text-gray-500 mb-3 line-clamp-2">'+(p.description||'')+'</p>';
        html += '<div class="flex items-center justify-between">';
        html += '<div>';
        html += '<span class="text-xl font-bold text-gray-900">'+CS+p.price.toFixed(2)+'</span>';
        if (hasDiscount) html += ' <span class="text-sm text-gray-400 line-through">'+CS+p.compare_price.toFixed(2)+'</span>';
        html += '</div>';
        html += '<button onclick="addToCart(\\''+p.id+'\\')" class="w-10 h-10 rounded-full text-white flex items-center justify-center hover:scale-110 transition-transform" style="background:{brand_hex}"><i class="fa-solid fa-plus text-sm"></i></button>';
        html += '</div></div></div>';
    }}
    grid.innerHTML = html;
}}

function renderCategories(products) {{
    var cats = [];
    for (var i = 0; i < products.length; i++) {{
        if (products[i].category && cats.indexOf(products[i].category) === -1) cats.push(products[i].category);
    }}
    var bar = document.getElementById('categories-bar');
    if (!cats.length) {{ bar.classList.add('hidden'); return; }}
    bar.classList.remove('hidden');
    var html = '<button class="cat-btn px-4 py-2 rounded-full text-sm font-semibold bg-gray-900 text-white whitespace-nowrap" onclick="filterCategory(\\'\\')">Todos</button>';
    for (var j = 0; j < cats.length; j++) {{
        html += '<button class="cat-btn px-4 py-2 rounded-full text-sm font-semibold bg-gray-100 hover:bg-gray-200 whitespace-nowrap" onclick="filterCategory(\\''+cats[j]+'\\')">'+cats[j]+'</button>';
    }}
    bar.innerHTML = html;
}}

loadProducts();
</script>
</body></html>"""
    return HTMLResponse(content=html)
