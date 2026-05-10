from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from app.models.report import Report, HazardType, ReportStatus, SeverityLevel
from app.models.user import User, UserRole
from app.middleware.auth import get_current_user, require_official
from app.middleware.upload import validate_and_upload
from app.middleware.rate_limit import limiter
from app.services.nlp_service import nlp_service
from app.services.hotspot_service import hotspot_service
from app.routes.schemas.report_schemas import (
    CreateReportRequest, UpdateReportRequest,
)
from config.redis import cache
from fastapi import Request
from loguru import logger

router = APIRouter(prefix="/reports", tags=["Reports"])


def _serialize(report: Report) -> dict:
    d = report.dict()
    d["id"] = str(report.id)
    return d


# ──────────────────────────────────────────────
# GET /reports
# ──────────────────────────────────────────────
@router.get("")
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ReportStatus] = None,
    hazard_type: Optional[HazardType] = None,
    severity: Optional[SeverityLevel] = None,
    state: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    cache_key = f"reports:list:{page}:{limit}:{status}:{hazard_type}:{severity}:{state}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = {}
    if status:
        query["status"] = status
    if hazard_type:
        query["hazard_type"] = hazard_type
    if severity:
        query["severity"] = severity
    if state:
        query["state"] = state
    if from_date or to_date:
        query["created_at"] = {}
        if from_date:
            query["created_at"]["$gte"] = from_date
        if to_date:
            query["created_at"]["$lte"] = to_date

    # Geo-proximity filter using $nearSphere
    if longitude is not None and latitude is not None and radius_km is not None:
        query["location"] = {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": int(radius_km * 1000),
            }
        }

    skip = (page - 1) * limit
    reports = await Report.find(query).skip(skip).limit(limit).sort("-created_at").to_list()
    total = await Report.find(query).count()

    result = {
        "success": True,
        "data": [_serialize(r) for r in reports],
        "pagination": {"page": page, "limit": limit, "total": total, "pages": -(-total // limit)},
    }
    await cache.set(cache_key, result, ttl_seconds=60)
    return result


# ──────────────────────────────────────────────
# POST /reports
# ──────────────────────────────────────────────
@router.post("", status_code=201)
@limiter.limit("10/minute")
async def create_report(
    request: Request,
    body: CreateReportRequest,
    current_user: Optional[User] = Depends(get_current_user),
):
    # NLP analysis on description
    nlp_result = await nlp_service.analyze(body.description)

    report = Report(
        hazard_type=body.hazard_type,
        title=body.title,
        description=body.description,
        severity=body.severity,
        location={"type": "Point", "coordinates": [body.longitude, body.latitude]},
        location_name=body.location_name,
        state=body.state,
        district=body.district,
        incident_time=body.incident_time,
        reporter_id=str(current_user.id) if current_user else None,
        reporter_name=body.reporter_name or (current_user.name if current_user else None),
        reporter_phone=body.reporter_phone,
        nlp_urgency_score=nlp_result.get("urgency_score", 0.0),
        nlp_extracted_entities=nlp_result.get("entities", {}),
        language_detected=nlp_result.get("language", "en"),
    )
    await report.insert()

    if current_user:
        current_user.reports_count += 1
        await current_user.save()

    # Invalidate list cache
    await cache.delete_pattern("reports:list:*")

    # Trigger async hotspot recalculation
    try:
        await hotspot_service.update_for_area(body.latitude, body.longitude)
    except Exception as e:
        logger.warning(f"Hotspot update failed after report creation: {e}")

    return {"success": True, "data": _serialize(report)}


# ──────────────────────────────────────────────
# POST /reports/{id}/media
# ──────────────────────────────────────────────
@router.post("/{report_id}/media")
async def upload_report_media(
    report_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    report = await Report.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_id != str(current_user.id) and current_user.role not in (
        UserRole.OFFICIAL, UserRole.ANALYST, UserRole.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Not authorised to upload to this report")

    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files per report")

    uploaded = []
    for file in files:
        result = await validate_and_upload(file, folder="incois/reports")
        uploaded.append(result)
        report.media_urls.append(result["url"])
        report.media_types.append(result["media_type"])

    report.updated_at = datetime.utcnow()
    await report.save()
    return {"success": True, "uploaded": uploaded}


# ──────────────────────────────────────────────
# GET /reports/{id}
# ──────────────────────────────────────────────
@router.get("/{report_id}")
async def get_report(report_id: str):
    cache_key = f"reports:{report_id}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    result = {"success": True, "data": _serialize(report)}
    await cache.set(cache_key, result, ttl_seconds=120)
    return result


# ──────────────────────────────────────────────
# PUT /reports/{id} — Officials/Admins verify/reject
# ──────────────────────────────────────────────
@router.put("/{report_id}")
async def update_report(
    report_id: str,
    body: UpdateReportRequest,
    current_user: User = Depends(require_official),
):
    report = await Report.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if body.status:
        report.status = body.status
        if body.status == ReportStatus.VERIFIED:
            report.verified_by = str(current_user.id)
            report.verified_at = datetime.utcnow()
            # Increment reporter's verified count
            if report.reporter_id:
                reporter = await User.get(report.reporter_id)
                if reporter:
                    reporter.verified_reports_count += 1
                    await reporter.save()
        if body.status == ReportStatus.REJECTED:
            report.rejection_reason = body.rejection_reason

    if body.severity:
        report.severity = body.severity

    report.updated_at = datetime.utcnow()
    await report.save()

    await cache.delete(f"reports:{report_id}")
    await cache.delete_pattern("reports:list:*")

    return {"success": True, "data": _serialize(report)}


# ──────────────────────────────────────────────
# DELETE /reports/{id}
# ──────────────────────────────────────────────
@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    report = await Report.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_id != str(current_user.id) and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorised to delete this report")

    await report.delete()
    await cache.delete(f"reports:{report_id}")
    await cache.delete_pattern("reports:list:*")

    return {"success": True, "message": "Report deleted"}
