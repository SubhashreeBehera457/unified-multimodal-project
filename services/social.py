"""
services/social.py
──────────────────
Social media ingestion layer.

Architecture:
  External Source → Ingestion → Text Cleaning → DistilBERT → Verification State

Supported sources:
  ✅ Manual input (always available — for demo/testing)
  ✅ GDELT GKG (public, no auth — disaster keyword news articles)
  ⚙️  X (Twitter) API v2 (requires X_BEARER_TOKEN)
  ⚙️  Reddit API (requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET)

Verification states (these are DistilBERT model outputs — not independently verified facts):
  UNVERIFIED          → Not yet processed by DistilBERT
  LIKELY GENUINE      → DistilBERT P(genuine) ≥ 0.65
  UNCERTAIN           → 0.35 ≤ P(genuine) < 0.65
  LIKELY MISLEADING   → P(genuine) < 0.35
  VERIFIED INCIDENT   → Manually confirmed OR created as incident

IMPORTANT DISCLAIMER:
  MODEL CONFIDENCE ≠ FACTUAL TRUTH.
  A high DistilBERT score means the text resembles real disaster tweets,
  NOT that the event is actually occurring.
"""
import re
import requests
from datetime import datetime
from typing import Optional
from services.config import (
    X_BEARER_TOKEN,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    api_configured,
)


# ── DISASTER KEYWORDS for filtering ─────────────────────────────────────────
DISASTER_KEYWORDS = [
    "flood", "cyclone", "storm", "heavy rain", "waterlogging",
    "bridge collapse", "landslide", "evacuation", "rescue",
    "odisha flood", "bhubaneswar flood", "earthquake", "tsunami",
    "disaster", "emergency", "stranded", "rescue operation",
    "dam burst", "inundation", "cloudburst",
]


def clean_text(text: str) -> str:
    """Remove URLs, extra whitespace, special characters from report text."""
    text = re.sub(r"http\S+|www\S+", "", text)      # remove URLs
    text = re.sub(r"@\w+", "", text)                  # remove @mentions
    text = re.sub(r"#(\w+)", r"\1", text)             # keep hashtag text
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_disaster_keyword(text: str) -> bool:
    """Return True if the text contains any disaster keyword (case-insensitive)."""
    lower = text.lower()
    return any(kw in lower for kw in DISASTER_KEYWORDS)


# ── X / Twitter API ──────────────────────────────────────────────────────────
def fetch_x_reports(
    query: str = "flood OR cyclone OR disaster OR rescue OR evacuation -is:retweet lang:en",
    max_results: int = 10,
) -> dict:
    """
    Fetch recent tweets matching disaster keywords via X API v2.
    Requires X_BEARER_TOKEN environment variable.

    Returns:
        {
            "source": "X_LIVE" | "NOT_CONFIGURED" | "ERROR",
            "configured": bool,
            "reports": list[dict],
            "error": str | None,
            "fetched_at": str,
        }
    """
    if not api_configured("x"):
        return {
            "source": "NOT_CONFIGURED",
            "configured": False,
            "reports": [],
            "error": "X_BEARER_TOKEN environment variable not set. See .env.example.",
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,text,geo,public_metrics",
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=8)
        if r.status_code == 401:
            return {
                "source": "ERROR",
                "configured": True,
                "reports": [],
                "error": "X API 401 Unauthorized — check your bearer token.",
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
            }
        if r.status_code != 200:
            return {
                "source": "ERROR",
                "configured": True,
                "reports": [],
                "error": f"X API returned HTTP {r.status_code}: {r.text[:200]}",
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
            }
        data = r.json()
        reports = []
        for tweet in data.get("data", []):
            text = clean_text(tweet.get("text", ""))
            if not text:
                continue
            reports.append({
                "text": text,
                "raw_text": tweet.get("text", ""),
                "source_platform": "X (Twitter)",
                "tweet_id": tweet.get("id"),
                "created_at": tweet.get("created_at", ""),
                "ingested_at": datetime.now().strftime("%H:%M:%S"),
                "verification_status": "UNVERIFIED",
                "is_genuine": None,
                "credibility_score": None,
            })
        return {
            "source": "X_LIVE",
            "configured": True,
            "reports": reports,
            "error": None,
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as e:
        return {
            "source": "ERROR",
            "configured": True,
            "reports": [],
            "error": str(e),
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }


# ── Reddit API ───────────────────────────────────────────────────────────────
def fetch_reddit_reports(
    subreddits: list = None,
    max_results: int = 10,
) -> dict:
    """
    Fetch recent posts from disaster-related subreddits.
    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.

    Returns same structure as fetch_x_reports.
    """
    if subreddits is None:
        subreddits = ["floods", "naturaldisasters", "india", "odisha"]

    if not api_configured("reddit"):
        return {
            "source": "NOT_CONFIGURED",
            "configured": False,
            "reports": [],
            "error": "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set. See .env.example.",
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }

    # Reddit OAuth token
    try:
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        token_r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": REDDIT_USER_AGENT},
            timeout=6,
        )
        if token_r.status_code != 200:
            return {
                "source": "ERROR",
                "configured": True,
                "reports": [],
                "error": f"Reddit auth failed: HTTP {token_r.status_code}",
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
            }
        token = token_r.json().get("access_token")
        headers = {"Authorization": f"bearer {token}", "User-Agent": REDDIT_USER_AGENT}

        reports = []
        for sub in subreddits:
            if len(reports) >= max_results:
                break
            r = requests.get(
                f"https://oauth.reddit.com/r/{sub}/new",
                headers=headers,
                params={"limit": 10},
                timeout=6,
            )
            if r.status_code != 200:
                continue
            posts = r.json().get("data", {}).get("children", [])
            for post in posts:
                data = post.get("data", {})
                text = clean_text(f"{data.get('title', '')} {data.get('selftext', '')}")
                if not text or not contains_disaster_keyword(text):
                    continue
                reports.append({
                    "text": text[:500],
                    "raw_text": data.get("title", ""),
                    "source_platform": f"Reddit r/{sub}",
                    "created_at": datetime.fromtimestamp(
                        data.get("created_utc", 0)
                    ).strftime("%Y-%m-%d %H:%M"),
                    "ingested_at": datetime.now().strftime("%H:%M:%S"),
                    "verification_status": "UNVERIFIED",
                    "is_genuine": None,
                    "credibility_score": None,
                    "reddit_url": f"https://reddit.com{data.get('permalink', '')}",
                })
        return {
            "source": "REDDIT_LIVE",
            "configured": True,
            "reports": reports,
            "error": None,
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as e:
        return {
            "source": "ERROR",
            "configured": True,
            "reports": [],
            "error": str(e),
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }


# ── GDELT GKG Public Feed ────────────────────────────────────────────────────
def fetch_gdelt_news(max_results: int = 10) -> dict:
    """
    Fetch disaster-related news articles from GDELT GKG (Global Knowledge Graph).
    Public, no authentication required.
    Uses the GDELT DOC 2.0 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

    Returns same structure as fetch_x_reports.
    """
    query = "flood OR cyclone OR earthquake OR tsunami OR landslide"
    url = (
        "https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={requests.utils.quote(query)}"
        "&mode=ArtList&maxrecords=25&format=json"
        "&sourcelang=english"
        "&timespan=1d"
    )
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return _gdelt_error(f"GDELT returned HTTP {r.status_code}")
        data = r.json()
        articles = data.get("articles", []) or []

        reports = []
        for art in articles[:max_results]:
            title = clean_text(art.get("title", ""))
            if not title:
                continue
            reports.append({
                "text": title,
                "raw_text": title,
                "source_platform": f"GDELT News ({art.get('domain', 'unknown')})",
                "created_at": art.get("seendate", "")[:16].replace("T", " "),
                "ingested_at": datetime.now().strftime("%H:%M:%S"),
                "verification_status": "UNVERIFIED",
                "is_genuine": None,
                "credibility_score": None,
                "url": art.get("url", ""),
            })
        return {
            "source": "GDELT_LIVE",
            "configured": True,
            "reports": reports,
            "error": None,
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as e:
        return _gdelt_error(str(e))


def _gdelt_error(msg: str) -> dict:
    return {
        "source": "UNAVAILABLE",
        "configured": True,
        "reports": [],
        "error": msg,
        "fetched_at": datetime.now().strftime("%H:%M:%S"),
    }


# ── Verification status helper ────────────────────────────────────────────────
def determine_verification_status(prob_genuine: float) -> str:
    """
    Map DistilBERT P(genuine) → verification status label.
    This is a model output label — not an independent fact check.
    """
    if prob_genuine >= 0.65:
        return "LIKELY GENUINE"
    elif prob_genuine >= 0.35:
        return "UNCERTAIN"
    else:
        return "LIKELY MISLEADING"
