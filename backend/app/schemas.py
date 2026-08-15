from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str
    company_name: str
    industry: str
    system_prompt: str = "Asistente"
    main_objective: str = ""
    escalation_email: str = ""


class WebsiteGenerationRequest(BaseModel):
    industry: str
    objective: str
    audience: str
    tone: str
    package: str = "full"
    brand_hex: str = "#2563eb"
    brand_secondary: str = "#764ba2"
    visual_style: str = "moderno"
    page_type: str = "landing"
    calendly_url: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=254)


class CheckoutRequest(BaseModel):
    tenant_id: str
    company_name: str
    industry: str
    system_prompt: str = "Asistente"
    main_objective: str = ""
    escalation_email: str = ""
    objective: str = ""
    audience: str = ""
    tone: str = "amigable"
    package: str = "full"
    visual_style: str = "moderno"
    page_type: str = "landing"
    provider: str = "demo"
    calendly_url: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: str = ""
