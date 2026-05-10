"""
Hotspot generation service using DBSCAN on geotagged report coordinates.

Algorithm:
  1. Pull recent verified/pending reports
  2. DBSCAN cluster on (lat, lon) with configurable eps & min_samples
  3. Compute centroid, convex hull, weighted density score
  4. Upsert Hotspot documents
"""

import math
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger

try:
    import numpy as np
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed — hotspot clustering disabled")

from app.models.report import Report, ReportStatus, SeverityLevel
from app.models.hotspot import Hotspot, HotspotSeverity

# Severity → numeric weight for density scoring
SEVERITY_WEIGHT = {
    SeverityLevel.LOW: 1.0,
    SeverityLevel.MEDIUM: 2.0,
    SeverityLevel.HIGH: 4.0,
    SeverityLevel.CRITICAL: 8.0,
}

# DBSCAN: ~2 km radius in radians (for haversine metric)
EARTH_RADIUS_KM = 6371.0
EPS_KM = 2.0
EPS_RAD = EPS_KM / EARTH_RADIUS_KM
MIN_SAMPLES = 3


def _recency_weight(created_at: datetime, now: datetime) -> float:
    """Exponential decay over 7 days."""
    age_hours = (now - created_at).total_seconds() / 3600
    return math.exp(-age_hours / (7 * 24))


def _severity_to_hotspot(max_weight: float) -> HotspotSeverity:
    if max_weight >= SEVERITY_WEIGHT[SeverityLevel.CRITICAL]:
        return HotspotSeverity.CRITICAL
    if max_weight >= SEVERITY_WEIGHT[SeverityLevel.HIGH]:
        return HotspotSeverity.HIGH
    if max_weight >= SEVERITY_WEIGHT[SeverityLevel.MEDIUM]:
        return HotspotSeverity.MEDIUM
    return HotspotSeverity.LOW


class HotspotService:
    async def _get_recent_reports(self, since_days: int = 7) -> List[Report]:
        since = datetime.utcnow() - timedelta(days=since_days)
        return await Report.find(
            {
                "status": {"$in": [ReportStatus.PENDING, ReportStatus.VERIFIED]},
                "created_at": {"$gte": since},
            }
        ).to_list()

    async def update_for_area(self, lat: float, lon: float, radius_km: float = 50.0):
        """Recalculate hotspots in a local area after a new report is submitted."""
        reports = await self._get_recent_reports()
        # Filter to area
        def in_area(r: Report) -> bool:
            coords = r.location.get("coordinates", [0, 0])
            dlat = coords[1] - lat
            dlon = coords[0] - lon
            return math.sqrt(dlat**2 + dlon**2) * 111 < radius_km

        area_reports = [r for r in reports if in_area(r)]
        if area_reports:
            await self._cluster_and_save(area_reports)

    async def recalculate_all(self) -> int:
        """Full recalculation of all hotspots. Returns count of hotspots saved."""
        reports = await self._get_recent_reports()
        if not reports:
            return 0
        return await self._cluster_and_save(reports)

    async def _cluster_and_save(self, reports: List[Report]) -> int:
        if not HAS_SKLEARN or len(reports) < MIN_SAMPLES:
            return 0

        now = datetime.utcnow()
        coords = []
        for r in reports:
            c = r.location.get("coordinates", [0, 0])
            coords.append([math.radians(c[1]), math.radians(c[0])])  # lat, lon in radians

        X = np.array(coords)
        db = DBSCAN(eps=EPS_RAD, min_samples=MIN_SAMPLES, metric="haversine").fit(X)

        labels = db.labels_
        unique_labels = set(labels) - {-1}

        saved = 0
        for label in unique_labels:
            mask = labels == label
            cluster_reports = [r for r, m in zip(reports, mask) if m]

            # Centroid
            cluster_coords = [r.location["coordinates"] for r in cluster_reports]
            centroid_lon = sum(c[0] for c in cluster_coords) / len(cluster_coords)
            centroid_lat = sum(c[1] for c in cluster_coords) / len(cluster_coords)

            # Weighted density score
            density = sum(
                SEVERITY_WEIGHT.get(r.severity, 1.0) * _recency_weight(r.created_at, now)
                for r in cluster_reports
            )

            # Dominant hazard
            hazard_counts: dict = {}
            for r in cluster_reports:
                hazard_counts[r.hazard_type] = hazard_counts.get(r.hazard_type, 0) + 1
            dominant_hazard = max(hazard_counts, key=hazard_counts.get)
            all_hazards = list(hazard_counts.keys())

            max_weight = max(SEVERITY_WEIGHT.get(r.severity, 1.0) for r in cluster_reports)
            severity = _severity_to_hotspot(max_weight)

            first_report = min(cluster_reports, key=lambda r: r.created_at)
            last_report  = max(cluster_reports, key=lambda r: r.created_at)

            # Try to find an existing active hotspot nearby and update it
            existing = await Hotspot.find_one({
                "center": {
                    "$nearSphere": {
                        "$geometry": {"type": "Point", "coordinates": [centroid_lon, centroid_lat]},
                        "$maxDistance": int(EPS_KM * 1000),
                    }
                },
                "is_active": True,
            })

            hotspot_data = dict(
                center={"type": "Point", "coordinates": [centroid_lon, centroid_lat]},
                report_count=len(cluster_reports),
                severity=severity,
                dominant_hazard_type=str(dominant_hazard),
                hazard_types=[str(h) for h in all_hazards],
                density_score=round(density, 4),
                first_report_at=first_report.created_at,
                last_report_at=last_report.created_at,
                is_active=True,
                updated_at=now,
                state=last_report.state,
                district=last_report.district,
                location_name=last_report.location_name,
            )

            if existing:
                for k, v in hotspot_data.items():
                    setattr(existing, k, v)
                await existing.save()
            else:
                hotspot = Hotspot(**hotspot_data)
                await hotspot.insert()

            saved += 1

        logger.info(f"HotspotService: saved/updated {saved} hotspots")
        return saved


hotspot_service = HotspotService()
