from fastapi import APIRouter, Query, Depends
from typing import Optional
from app.models.social_post import SocialPost, SocialPlatform
from app.middleware.auth import require_analyst
from app.services.social_media_service import social_service
from config.redis import cache

router = APIRouter(prefix="/social", tags=["Social Media"])


@router.get("/trends")
async def get_trends(
    platform: Optional[SocialPlatform] = None,
    hours: int = Query(24, ge=1, le=168),
    _=Depends(require_analyst),
):
    cache_key = f"social:trends:{platform}:{hours}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    trends = await social_service.get_trends(platform=platform, hours=hours)
    result = {"success": True, "data": trends}
    await cache.set(cache_key, result, ttl_seconds=300)
    return result


@router.get("/posts")
async def list_hazard_posts(
    platform: Optional[SocialPlatform] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    min_urgency: float = Query(0.5, ge=0.0, le=1.0),
    _=Depends(require_analyst),
):
    query = {"is_hazard_related": True, "urgency_score": {"$gte": min_urgency}}
    if platform:
        query["platform"] = platform

    skip = (page - 1) * limit
    posts = await SocialPost.find(query).skip(skip).limit(limit).sort("-urgency_score").to_list()
    total = await SocialPost.find(query).count()

    return {
        "success": True,
        "data": [p.dict() for p in posts],
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.post("/fetch")
async def trigger_social_fetch(_=Depends(require_analyst)):
    """Manually trigger social media ingestion."""
    result = await social_service.fetch_and_analyze()
    await cache.delete_pattern("social:*")
    return {"success": True, "fetched": result}
