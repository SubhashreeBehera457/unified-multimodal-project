"""
backend/api/social.py
─────────────────────
Social media & news intelligence ingestion endpoint.
Genuinely respects API configuration; reports NOT CONFIGURED when credentials are missing.
"""
from fastapi import APIRouter, Query
from services.config import api_configured
from services.social import fetch_gdelt_news, fetch_x_reports, fetch_reddit_reports
from backend.state import state_manager

router = APIRouter(prefix="/social", tags=["Social Intelligence"])


@router.get("/gdelt")
def get_gdelt_reports(max_results: int = Query(10, ge=1, le=50)):
    """Fetch live disaster news via GDELT DOC 2.0 API (public)."""
    data = fetch_gdelt_news(max_results=max_results)
    if data.get("source") == "GDELT_LIVE":
        for report in data.get("reports", []):
            state_manager.add_report(report)
    return data


@router.get("/x")
def get_x_reports(query: str = "flood OR cyclone OR disaster", max_results: int = 10):
    """Fetch live posts from X (Twitter) if configured."""
    if not api_configured("x"):
        return {
            "status": "NOT_CONFIGURED",
            "source": "UNAVAILABLE",
            "message": "X/Twitter API is not configured. Add X_BEARER_TOKEN to environment.",
            "reports": [],
        }
    return fetch_x_reports(query=query, max_results=max_results)


@router.get("/reddit")
def get_reddit_reports(max_results: int = 10):
    """Fetch live posts from Reddit if configured."""
    if not api_configured("reddit"):
        return {
            "status": "NOT_CONFIGURED",
            "source": "UNAVAILABLE",
            "message": "Reddit API is not configured. Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to environment.",
            "reports": [],
        }
    return fetch_reddit_reports(max_results=max_results)


@router.get("/reports")
def get_all_reports():
    """Return all ingested reports in the current session."""
    return {
        "count": len(state_manager.get_reports()),
        "reports": state_manager.get_reports(),
    }
