# Testimonios con fotos - memoria de trabajo (2026-08-17)

## Qué se hizo
- Fotos reales de testimonios via pollinations.ai en las 3 plantillas.
- LLM genera `photo_prompt` por cada testimonial (ej: "profesional mexicano sonriente retrato corporativo").
- `website_service.py` convierte photo_prompt a URL de pollinations (200x200px, seed basado en el nombre).
- Templates muestran `<img>` con la foto, con fallback a initial si no hay foto.
- Sección de testimonios agregada a `services.html` y `portfolio.html` (antes solo existía en landing.html).

## Archivos modificados
- `backend/app/services/llm_service.py` — Campo `photo_prompt` en prompt principal y fallback
- `backend/app/services/website_service.py` — Generación de URLs de foto desde photo_prompt
- `backend/app/templates/landing.html` — Foto en vez de inicial en testimonios
- `backend/app/templates/services.html` — Nueva sección de testimonios con fotos
- `backend/app/templates/portfolio.html` — Nueva sección de testimonios con fotos

## Siguiente mejora
- Formulario de contacto funcional que deje leads en el panel admin.
