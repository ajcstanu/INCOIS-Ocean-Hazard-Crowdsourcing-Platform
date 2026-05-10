from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.report import HazardType, SeverityLevel, ReportStatus


class CoordinatesSchema(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)


class CreateReportRequest(BaseModel):
    hazard_type: HazardType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    location_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    incident_time: Optional[datetime] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None


class UpdateReportRequest(BaseModel):
    status: Optional[ReportStatus] = None
    rejection_reason: Optional[str] = None
    severity: Optional[SeverityLevel] = None


class ReportFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: Optional[ReportStatus] = None
    hazard_type: Optional[HazardType] = None
    severity: Optional[SeverityLevel] = None
    state: Optional[str] = None
    # Geo filter
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    radius_km: Optional[float] = None
    # Date filter
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
