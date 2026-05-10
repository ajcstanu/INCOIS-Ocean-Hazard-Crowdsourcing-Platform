from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from app.models.report import Report, HazardType, ReportStatus, SeverityLevel
from app.models.hotspot import Hotspot
from app.models.social_post import SocialPost
from app.middleware.auth import require_analyst
from config.redis import cache

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_analytics(
    days: int = Query(7, ge=1, le=90),
    _=Depends(require_analyst),
):
    cache_key = f"analytics:dashboard:{days}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    since = datetime.utcnow() - timedelta(days=days)
    total_reports = await Report.find({"created_at": {"$gte": since}}).count()
    verified     = await Report.find({"status": ReportStatus.VERIFIED, "created_at": {"$gte": since}}).count()
    pending      = await Report.find({"status": ReportStatus.PENDING,  "created_at": {"$gte": since}}).count()
    critical     = await Report.find({"severity": SeverityLevel.CRITICAL, "created_at": {"$gte": since}}).count()
    active_spots = await Hotspot.find({"is_active": True}).count()
    social_hits  = await SocialPost.find({"is_hazard_related": True, "collected_at": {"$gte": since}}).count()

    # Breakdown by hazard type
    by_hazard = {}
    for h in HazardType:
        by_hazard[h.value] = await Report.find(
            {"hazard_type": h, "created_at": {"$gte": since}}
        ).count()

    result = {
        "success": True,
        "period_days": days,
        "data": {
            "total_reports": total_reports,
            "verified_reports": verified,
            "pending_reports": pending,
            "critical_reports": critical,
            "active_hotspots": active_spots,
            "social_hazard_mentions": social_hits,
            "verification_rate": round(verified / total_reports * 100, 1) if total_reports else 0,
            "by_hazard_type": by_hazard,
        },
    }
    await cache.set(cache_key, result, ttl_seconds=300)
    return result


@router.get("/trends")
async def report_trends(
    days: int = Query(30, ge=7, le=365),
    _=Depends(require_analyst),
):
    """Daily report counts for the given period."""
    cache_key = f"analytics:trends:{days}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    since = datetime.utcnow() - timedelta(days=days)
    reports = await Report.find({"created_at": {"$gte": since}}).to_list()

    # Bucket by date
    buckets: dict = {}
    for r in reports:
        day = r.created_at.strftime("%Y-%m-%d")
        buckets[day] = buckets.get(day, 0) + 1

    result = {
        "success": True,
        "data": [{"date": d, "count": c} for d, c in sorted(buckets.items())],
    }
    await cache.set(cache_key, result, ttl_seconds=600)
    return result
