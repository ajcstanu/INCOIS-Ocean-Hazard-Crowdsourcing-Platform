from fastapi import APIRouter, Query
from typing import Optional
from app.models.hotspot import Hotspot
from app.services.hotspot_service import hotspot_service
from app.middleware.auth import require_admin
from config.redis import cache
from fastapi import Depends

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])


@router.get("")
async def list_hotspots(
    active_only: bool = True,
    state: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    radius_km: Optional[float] = Query(None, description="Filter by radius (km)"),
):
    cache_key = f"hotspots:list:{active_only}:{state}:{longitude}:{latitude}:{radius_km}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = {}
    if active_only:
        query["is_active"] = True
    if state:
        query["state"] = state

    if longitude is not None and latitude is not None and radius_km is not None:
        query["center"] = {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": int(radius_km * 1000),
            }
        }

    hotspots = await Hotspot.find(query).sort("-density_score").to_list()

    result = {
        "success": True,
        "data": [
            {
                "id": str(h.id),
                "center": h.center,
                "boundary": h.boundary,
                "severity": h.severity,
                "dominant_hazard_type": h.dominant_hazard_type,
                "report_count": h.report_count,
                "density_score": h.density_score,
                "social_mention_count": h.social_mention_count,
                "state": h.state,
                "location_name": h.location_name,
                "last_report_at": h.last_report_at,
            }
            for h in hotspots
        ],
        "total": len(hotspots),
    }
    await cache.set(cache_key, result, ttl_seconds=120)
    return result


@router.get("/{hotspot_id}")
async def get_hotspot(hotspot_id: str):
    hotspot = await Hotspot.get(hotspot_id)
    if not hotspot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Hotspot not found")
    return {"success": True, "data": hotspot.dict()}


@router.post("/recalculate")
async def trigger_recalculate(_=Depends(require_admin)):
    """Admin endpoint to manually trigger full hotspot recalculation."""
    count = await hotspot_service.recalculate_all()
    await cache.delete_pattern("hotspots:*")
    return {"success": True, "message": f"Recalculated {count} hotspots"}
