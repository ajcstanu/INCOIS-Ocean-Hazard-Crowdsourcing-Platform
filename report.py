from beanie import Document, Indexed, Link
from pydantic import Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class HazardType(str, Enum):
    TSUNAMI = "tsunami"
    STORM_SURGE = "storm_surge"
    HIGH_WAVES = "high_waves"
    ROGUE_WAVE = "rogue_wave"
    COASTAL_FLOODING = "coastal_flooding"
    OIL_SPILL = "oil_spill"
    ALGAL_BLOOM = "algal_bloom"
    STRONG_CURRENT = "strong_current"
    CYCLONE = "cyclone"
    WATERSPOUT = "waterspout"
    BEACH_CLOSURE = "beach_closure"
    OTHER = "other"


class ReportStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    RESOLVED = "resolved"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GeoPoint(dict):
    """GeoJSON Point helper."""
    def __init__(self, longitude: float, latitude: float):
        super().__init__(type="Point", coordinates=[longitude, latitude])


class Report(Document):
    # Reporter info
    reporter_id: Optional[str] = None     # None for anonymous
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None

    # Hazard details
    hazard_type: HazardType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    severity: SeverityLevel = SeverityLevel.MEDIUM

    # Location
    location: dict = Field(...)            # GeoJSON Point {type, coordinates}
    location_name: Optional[str] = None   # Human-readable address
    state: Optional[str] = None
    district: Optional[str] = None

    # Media
    media_urls: List[str] = []
    media_types: List[str] = []           # "image" | "video"

    # Status & verification
    status: ReportStatus = ReportStatus.PENDING
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # NLP analysis
    nlp_urgency_score: float = 0.0        # 0.0 – 1.0
    nlp_extracted_entities: dict = {}
    language_detected: str = "en"

    # Source
    source: str = "citizen"               # "citizen" | "social_media" | "official"
    source_url: Optional[str] = None

    # Cluster/hotspot linkage
    hotspot_id: Optional[str] = None
    incident_cluster_id: Optional[str] = None

    # Timestamps
    incident_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "reports"
        indexes = [
            [("location", "2dsphere")],
            "status",
            "hazard_type",
            "severity",
            "reporter_id",
            "created_at",
            "hotspot_id",
        ]
