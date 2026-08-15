import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.deps import DATA_DIR, PRICES, auth_service, read_json_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/analytics/global")
async def get_global_analytics(current_user: dict = Depends(auth_service.get_current_user)):
    """Obtener métricas globales con datos para gráficas"""
    try:
        tenants = read_json_file(DATA_DIR / "tenants.json", [])
        conversations = read_json_file(DATA_DIR / "storage" / "conversations.json", [])
        leads = read_json_file(DATA_DIR / "storage" / "leads.json", [])

        total_tenants = len(tenants)
        total_conversations = len(conversations)
        total_leads = len(leads)

        industries_count = {}
        for t in tenants:
            ind = t.get("industry", "Sin especificar")
            industries_count[ind] = industries_count.get(ind, 0) + 1

        packages_count = {"full": 0, "web_chat": 0, "chat_only": 0, "seo_only": 0}
        for t in tenants:
            pkg = t.get("package", "sin_paquete")
            if pkg in packages_count:
                packages_count[pkg] += 1
            else:
                packages_count.setdefault(pkg, 1)
        packages_count = {k: v for k, v in packages_count.items() if v > 0}

        package_prices = PRICES
        paid_tenants = [t for t in tenants if t.get("payment_status") == "paid"]
        packages_count_paid = {}
        for t in paid_tenants:
            pkg = t.get("package", "sin_paquete")
            packages_count_paid[pkg] = packages_count_paid.get(pkg, 0) + 1
        total_revenue = sum(
            count * package_prices.get(pkg, 0) for pkg, count in packages_count_paid.items()
        )

        leads_by_day = {}
        today = datetime.now()
        for i in range(7):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            leads_by_day[day] = 0

        for lead in leads:
            lead_date = lead.get("timestamp", "")
            if lead_date:
                try:
                    day = lead_date.split("T")[0]
                    if day in leads_by_day:
                        leads_by_day[day] += 1
                except Exception:
                    pass

        leads_timeline = [
            {"date": k, "count": v}
            for k, v in sorted(leads_by_day.items())
        ]

        tenant_conversations = {}
        for conv in conversations:
            tid = conv.get("tenant_id", "")
            if tid:
                tenant_conversations[tid] = tenant_conversations.get(tid, 0) + 1

        top_tenants = sorted(
            tenant_conversations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        top_companies = []
        for tid, count in top_tenants:
            tenant = next((t for t in tenants if (t.get("tenant_id") or t.get("id")) == tid), None)
            name = tenant.get("company_name", tid) if tenant else tid
            top_companies.append({"name": name, "conversations": count})

        tenant_name_map = {t.get("tenant_id") or t.get("id"): t.get("company_name", "") for t in tenants}
        recent_leads = []
        for lead in sorted(leads, key=lambda l: l.get("timestamp", ""), reverse=True)[:10]:
            tid = lead.get("tenant_id", "")
            recent_leads.append({
                "email": lead.get("email", ""),
                "company": tenant_name_map.get(tid, tid),
                "question": lead.get("question", ""),
                "timestamp": lead.get("timestamp", "")
            })

        return {
            "status": "success",
            "metrics": {
                "total_tenants": total_tenants,
                "total_conversations": total_conversations,
                "total_leads": total_leads,
                "monthly_revenue_estimate": total_revenue,
                "paid_tenants": len(paid_tenants)
            },
            "charts": {
                "industries": industries_count,
                "packages": packages_count,
                "leads_timeline": leads_timeline,
                "top_companies": top_companies
            },
            "recent_leads": recent_leads
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
