from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class HotspotSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Hotspot(Document):
    # GeoJSON Point (centroid of cluster)
    center: dict = Field(...)
    # GeoJSON Polygon (convex hull of cluster)
    boundary: Optional[dict] = None

    # Cluster stats
    report_count: int = 0
    severity: HotspotSeverity = HotspotSeverity.LOW
    dominant_hazard_type: Optional[str] = None
    hazard_types: List[str] = []

    # Weighted score (severity + recency + social boost)
    density_score: float = 0.0
    social_boost_factor: float = 1.0

    # Location info
    state: Optional[str] = None
    district: Optional[str] = None
    location_name: Optional[str] = None

    # Social media signal
    social_mention_count: int = 0
    social_trend_score: float = 0.0

    # Lifecycle
    is_active: bool = True
    first_report_at: Optional[datetime] = None
    last_report_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "hotspots"
        indexes = [
            [("center", "2dsphere")],
            "is_active",
            "severity",
            "density_score",
        ]
