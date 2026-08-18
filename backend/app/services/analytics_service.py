import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ANALYTICS_DIR = DATA_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def _get_file(tenant_id: str) -> Path:
    return ANALYTICS_DIR / f"{tenant_id}.json"


def _read_analytics(tenant_id: str) -> dict:
    f = _get_file(tenant_id)
    if f.exists():
        try:
            with open(f, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {"page_views": [], "leads": [], "chat_sessions": []}


def _write_analytics(tenant_id: str, data: dict):
    f = _get_file(tenant_id)
    tmp = f.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    tmp.replace(f)


class AnalyticsService:

    def track_page_view(self, tenant_id: str, page: str = "/", referrer: str = "", country: str = ""):
        data = _read_analytics(tenant_id)
        data["page_views"].append({
            "page": page,
            "referrer": referrer,
            "country": country,
            "timestamp": datetime.now().isoformat(),
        })
        if len(data["page_views"]) > 10000:
            data["page_views"] = data["page_views"][-5000:]
        _write_analytics(tenant_id, data)

    def track_lead(self, tenant_id: str, email: str, source: str = ""):
        data = _read_analytics(tenant_id)
        data["leads"].append({
            "email": email,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        })
        _write_analytics(tenant_id, data)

    def track_chat(self, tenant_id: str, session_id: str = ""):
        data = _read_analytics(tenant_id)
        data["chat_sessions"].append({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        })
        if len(data["chat_sessions"]) > 5000:
            data["chat_sessions"] = data["chat_sessions"][-2500:]
        _write_analytics(tenant_id, data)

    def get_dashboard(self, tenant_id: str, days: int = 30) -> dict:
        data = _read_analytics(tenant_id)
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        recent_views = [v for v in data["page_views"] if v.get("timestamp", "") >= cutoff]
        recent_leads = [l for l in data["leads"] if l.get("timestamp", "") >= cutoff]
        recent_chats = [c for c in data["chat_sessions"] if c.get("timestamp", "") >= cutoff]

        today = datetime.now().strftime("%Y-%m-%d")
        today_views = sum(1 for v in recent_views if v.get("timestamp", "").startswith(today))

        pages = {}
        for v in recent_views:
            p = v.get("page", "/")
            pages[p] = pages.get(p, 0) + 1
        top_pages = sorted(pages.items(), key=lambda x: x[1], reverse=True)[:5]

        sources = {}
        for l in recent_leads:
            s = l.get("source", "direct")
            sources[s] = sources.get(s, 0) + 1

        daily_views = {}
        for v in recent_views:
            d = v.get("timestamp", "")[:10]
            daily_views[d] = daily_views.get(d, 0) + 1

        return {
            "total_views": len(recent_views),
            "today_views": today_views,
            "total_leads": len(recent_leads),
            "total_chats": len(recent_chats),
            "top_pages": [{"page": p, "views": c} for p, c in top_pages],
            "lead_sources": sources,
            "daily_views": [{"date": d, "views": c} for d, c in sorted(daily_views.items())],
        }


analytics_service = AnalyticsService()
