import os
import json
import zipfile
import shutil
import logging
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
WEBSITES_DIR = DATA_DIR / "websites"
EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ExportService:
    """Servicio para exportar sitios web completos en ZIP"""

    @staticmethod
    def _download_image(url, save_path):
        try:
            response = requests.get(url, timeout=15, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            logger.warning(f"No se pudo descargar {url}: {e}")
            return False

    @staticmethod
    def export_site(tenant_id):
        try:
            tenant_dir = WEBSITES_DIR / tenant_id
            if not tenant_dir.exists():
                return {"status": "error", "detail": "Sitio no encontrado"}

            site_data_file = tenant_dir / "site_data.json"
            if not site_data_file.exists():
                return {"status": "error", "detail": "Datos del sitio no encontrados"}

            with open(site_data_file, 'r', encoding='utf-8') as f:
                site_data = json.load(f)

            company_name = site_data.get("company_name", tenant_id)
            industry = site_data.get("industry", "general")

            export_name = f"{tenant_id}-{int(datetime.now().timestamp())}"
            temp_dir = EXPORTS_DIR / export_name
            temp_dir.mkdir(parents=True, exist_ok=True)

            assets_dir = temp_dir / "assets" / "images"
            assets_dir.mkdir(parents=True, exist_ok=True)

            images_map = {}
            hero_url = site_data.get("hero_image", "")
            if hero_url and hero_url.startswith("http"):
                local_path = "assets/images/hero.jpg"
                if ExportService._download_image(hero_url, temp_dir / local_path):
                    images_map[hero_url] = local_path

            about_url = site_data.get("about_image", "")
            if about_url and about_url.startswith("http"):
                local_path = "assets/images/about.jpg"
                if ExportService._download_image(about_url, temp_dir / local_path):
                    images_map[about_url] = local_path

            gallery = site_data.get("gallery_images", [])
            for idx, img_url in enumerate(gallery):
                if img_url and img_url.startswith("http"):
                    local_path = f"assets/images/gallery-{idx + 1}.jpg"
                    if ExportService._download_image(img_url, temp_dir / local_path):
                        images_map[img_url] = local_path

            original_html = tenant_dir / "index.html"
            with open(original_html, 'r', encoding='utf-8-sig') as f:
                html_content = f.read()

            for remote_url, local_path in images_map.items():
                html_content = html_content.replace(remote_url, local_path)

            with open(temp_dir / "index.html", 'w', encoding='utf-8-sig') as f:
                f.write(html_content)

            readme = f"""# {company_name} - Sitio Web Profesional\n\nSitio web generado para {company_name} ({industry}).\n\n## Instalación:\n1. Descomprime este ZIP\n2. Sube los archivos a public_html de tu hosting\n3. Accede a tu dominio\n\n## Chatbot Integrado\nEl chatbot ya está configurado. Tenant ID: {tenant_id}\n\nGenerado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
            with open(temp_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme)

            config = {"tenant_id": tenant_id, "company_name": company_name, "exported_at": datetime.now().isoformat()}
            with open(temp_dir / "config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            zip_path = EXPORTS_DIR / f"{export_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)

            shutil.rmtree(temp_dir)
            logger.info(f"✅ Sitio exportado: {zip_path.name}")

            return {
                "status": "success",
                "download_url": f"/data/exports/{zip_path.name}",
                "filename": zip_path.name,
                "size_mb": round(zip_path.stat().st_size / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.error(f"Error exportando sitio: {e}", exc_info=True)
            return {"status": "error", "detail": str(e)}