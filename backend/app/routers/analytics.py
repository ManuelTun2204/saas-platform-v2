import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.deps import DATA_DIR, PRICES, read_json_file, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/analytics/global")
async def get_global_analytics(current_user: dict = Depends(require_admin)):
    """Obtener métricas globales con datos para gráficas (solo admin)"""
    try:
        tenants = read_json_file(DATA_DIR / "tenants.json", [])
        conversations = read_json_file(DATA_DIR / "storage" / "conversations.json", [])
        leads = read_json_file(DATA_DIR / "storage" / "leads.json", [])
        orders = read_json_file(DATA_DIR / "storage" / "orders.json", [])
        llm_usage = read_json_file(DATA_DIR / "storage" / "llm_usage.json", [])

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

        # Ingresos reales desde las ordenes de pago
        paid_orders = [o for o in orders if o.get("status") == "paid"]
        revenue_total = round(sum(float(o.get("amount", 0) or 0) for o in paid_orders), 2)
        today = datetime.now()
        month_labels = []
        revenue_by_month = {}
        for i in range(5, -1, -1):
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            key = f"{y}-{m:02d}"
            month_labels.append(key)
            revenue_by_month[key] = 0.0
        for o in paid_orders:
            created = o.get("created_at", "")
            key = created[:7] if len(created) >= 7 else ""
            if key in revenue_by_month:
                try:
                    revenue_by_month[key] += float(o.get("amount", 0) or 0)
                except Exception:
                    pass
        revenue_monthly = [{"label": k, "amount": round(v, 2)} for k, v in revenue_by_month.items()]
        revenue_this_month = revenue_by_month.get(today.strftime("%Y-%m"), 0.0)
        orders_pending = len([o for o in orders if o.get("status") == "pending"])
        orders_cancelled = len([o for o in orders if o.get("status") == "cancelled"])

        # Costo de IA (LLM) acumulado desde el archivo de uso
        cost_total = 0.0
        cost_by_month = {key: 0.0 for key in month_labels}
        llm_calls_total = len(llm_usage)
        for rec in llm_usage:
            cost = rec.get("cost_usd")
            if cost is None:
                continue
            try:
                cost_total += float(cost)
            except Exception:
                pass
            created = rec.get("ts", "")
            key = created[:7] if len(created) >= 7 else ""
            if key in cost_by_month:
                try:
                    cost_by_month[key] += float(cost)
                except Exception:
                    pass
        llm_cost_monthly = [{"label": k, "amount": round(v, 4)} for k, v in cost_by_month.items()]
        llm_cost_this_month = round(cost_by_month.get(today.strftime("%Y-%m"), 0.0), 4)
        llm_calls_this_month = sum(
            1 for rec in llm_usage if rec.get("ts", "").startswith(today.strftime("%Y-%m"))
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
        leads_nuevos = sum(1 for l in leads if l.get("status", "nuevo") == "nuevo")
        leads_contactados = sum(1 for l in leads if l.get("status") == "contactado")
        leads_convertidos = sum(1 for l in leads if l.get("status") == "convertido")
        recent_leads = []
        for lead in sorted(leads, key=lambda l: l.get("timestamp", ""), reverse=True)[:10]:
            tid = lead.get("tenant_id", "")
            recent_leads.append({
                "email": lead.get("email", ""),
                "company": tenant_name_map.get(tid, tid),
                "question": lead.get("question", ""),
                "status": lead.get("status", "nuevo"),
                "timestamp": lead.get("timestamp", "")
            })

        return {
            "status": "success",
            "metrics": {
                "total_tenants": total_tenants,
                "total_conversations": total_conversations,
                "total_leads": total_leads,
                "leads_nuevos": leads_nuevos,
                "leads_contactados": leads_contactados,
                "leads_convertidos": leads_convertidos,
                "monthly_revenue_estimate": total_revenue,
                "paid_tenants": len(paid_tenants),
                "revenue_this_month": round(revenue_this_month, 2),
                "revenue_total": revenue_total,
                "orders_total": len(orders),
                "orders_pending": orders_pending,
                "orders_cancelled": orders_cancelled,
                "llm_cost_this_month": llm_cost_this_month,
                "llm_cost_total": round(cost_total, 4),
                "llm_calls_total": llm_calls_total,
                "llm_calls_this_month": llm_calls_this_month,
            },
            "charts": {
                "industries": industries_count,
                "packages": packages_count,
                "leads_timeline": leads_timeline,
                "top_companies": top_companies,
                "revenue_monthly": revenue_monthly,
                "llm_cost_monthly": llm_cost_monthly,
            },
            "recent_leads": recent_leads
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
