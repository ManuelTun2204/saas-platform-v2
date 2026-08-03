import asyncio
import sys
sys.path.append('backend')
from app.services.website_service import WebsiteService

async def test():
    service = WebsiteService()
    result = await service.generate_website(
        tenant_id="test-123",
        industry="Consultoría Financiera",
        objective="Captar leads de alto valor",
        audience="Empresarios y dueños de PYMES",
        tone="Profesional, confiable y exclusivo"
    )
    print("✅ RESULTADO:")
    print(f"Plantilla usada: {result['template_used']}")
    print(f"URL de vista previa: http://localhost:8000{result['preview_url']}")

asyncio.run(test())
