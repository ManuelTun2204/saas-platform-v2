# Escaparate de Plantillas - memoria de trabajo (2026-08-17)

## Qué se hizo
- Landing pública en `/landing` (ruta nueva en main.py) con escaparate de plantillas y generador.
- 4 sitios de showcase pre-generados: Restaurante (Moderno), Dentista (Vidrio/Glassmorphism), Tienda (Natural), Consultoría (Elegante).
- Cada tarjeta tiene: imagen preview (pollinations.ai), nombre, tag de estilo, descripción.
- Hover sobre tarjeta muestra: "Ver ejemplo" (abre sitio generado) + "Usar esta plantilla" (pre-llena el formulario).
- Hero section con headline + CTA "Crear mi sitio ahora" que lleva al formulario.
- Selector de estilos visuales con 6 opciones: Moderno, Natural, Elegante, Vidrio, Creativo, Minimalista.
- Precios visibles en el selector de paquetes ($399/$249/$99).
- Seprador visual "O configura tu propio sitio" entre showcase y formulario.
- Ruta `/landing` con headers anti-cache.

## Archivos modificados
- `backend/app/main.py` — Nueva ruta GET `/landing`
- `backend/app/static/index.html` — Reescritura completa: hero + escaparate + generador

## Showcase sites (en data/websites/)
- showcase-restaurante — Restaurante gourmet, estilo Moderno
- showcase-dentista — Clínica dental, estilo Glassmorphism/Vidrio
- showcase-tienda — Tienda de ropa, estilo Natural
- showcase-consultoria — Consultora empresarial, estilo Elegante

## Acceso
- Panel admin: `http://localhost:8000/`
- Landing pública: `http://localhost:8000/landing`

## Pendiente / siguiente
- Agregar más estilos si el usuario lo pide.
- Considerar crear una landing pública separada con dominio propio para ventas.
