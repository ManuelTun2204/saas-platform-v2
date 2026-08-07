import os
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY", "").strip()
        self.admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        self.from_email = "SaaS Platform <onboarding@resend.dev>"
        
        if not self.api_key:
            logger.warning("⚠️ RESEND_API_KEY no configurada. Las notificaciones de email estarán desactivadas.")
        elif not self.api_key.startswith("re_"):
            logger.warning("⚠️ RESEND_API_KEY inválida. Debe empezar con 're_'")
        else:
            logger.info(f"✅ EmailService configurado. Notificaciones a: {self.admin_email}")

    async def send_lead_notification(self, tenant_id: str, company_name: str, lead_email: str, question: str, answer: str):
        """Envía notificación al admin cuando se captura un lead"""
        if not self.api_key or not self.admin_email:
            logger.warning("Email no enviado: falta configuración")
            return False
        
        try:
            subject = f"🎯 Nuevo Lead Capturado - {company_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .content {{ padding: 30px; }}
                    .lead-info {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #667eea; }}
                    .label {{ font-weight: bold; color: #333; margin-bottom: 5px; }}
                    .value {{ color: #555; margin-bottom: 15px; }}
                    .cta {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 Nuevo Lead Capturado</h1>
                        <p>Un cliente potencial mostró interés en {company_name}</p>
                    </div>
                    <div class="content">
                        <div class="lead-info">
                            <div class="label">📧 Email del Cliente:</div>
                            <div class="value"><a href="mailto:{lead_email}">{lead_email}</a></div>
                            
                            <div class="label">💬 Pregunta:</div>
                            <div class="value">{question}</div>
                            
                            <div class="label">🤖 Respuesta del Chatbot:</div>
                            <div class="value">{answer}</div>
                            
                            <div class="label">🏢 Empresa:</div>
                            <div class="value">{company_name} (ID: {tenant_id})</div>
                            
                            <div class="label">🕐 Fecha y Hora:</div>
                            <div class="value">{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
                        </div>
                        
                        <p><strong>💡 Recomendación:</strong> Contacta al cliente lo antes posible. Los leads que reciben respuesta en menos de 1 hora tienen 7x más probabilidad de conversión.</p>
                        
                        <a href="http://localhost:8000" class="cta">Ver Panel de Administración</a>
                    </div>
                    <div class="footer">
                        <p>Notificación automática de SaaS Platform V2</p>
                        <p>Para desactivar estas notificaciones, edita ADMIN_EMAIL en tu .env</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [self.admin_email],
                        "subject": subject,
                        "html": html_content
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Email de lead enviado: {lead_email} → {self.admin_email}")
                    return True
                else:
                    logger.error(f"❌ Error enviando email: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error en send_lead_notification: {e}")
            return False