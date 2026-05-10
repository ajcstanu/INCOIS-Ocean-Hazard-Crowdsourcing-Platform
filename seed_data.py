"""
Seed script: populates the DB with test users and sample reports.
Usage: python -m app.utils.seed_data
"""

import asyncio
from datetime import datetime, timedelta
import random

from config.database import connect_db
from app.models.user import User, UserRole, UserLanguage
from app.models.report import Report, HazardType, SeverityLevel, ReportStatus
from app.utils.security import hash_password

# Sample coastal coordinates (India)
COASTAL_POINTS = [
    (80.2707, 13.0827),  # Chennai
    (73.8567, 18.5204),  # Mumbai area
    (77.5946, 12.9716),  # Bangalore (not coastal but for testing)
    (80.9462, 14.9091),  # Visakhapatnam
    (76.2673, 9.9312),   # Kochi
    (85.0985, 20.2961),  # Bhubaneswar
    (79.8447, 11.9416),  # Cuddalore
    (74.8554, 15.3647),  # Karwar
]


async def seed():
    await connect_db()

    # Clear existing data
    await User.find_all().delete()
    await Report.find_all().delete()
    print("🗑  Cleared existing data")

    # Seed users
    users_data = [
        dict(name="Admin User",    email="admin@incois.gov.in",    role=UserRole.ADMIN,    language=UserLanguage.EN),
        dict(name="Ananya Sharma", email="analyst@incois.gov.in",  role=UserRole.ANALYST,  language=UserLanguage.HI),
        dict(name="Ravi Kumar",    email="official@incois.gov.in", role=UserRole.OFFICIAL, language=UserLanguage.TE),
        dict(name="Priya Nair",    email="citizen1@example.com",   role=UserRole.CITIZEN,  language=UserLanguage.ML),
        dict(name="Suresh Babu",   email="citizen2@example.com",   role=UserRole.CITIZEN,  language=UserLanguage.TA),
    ]

    created_users = []
    for ud in users_data:
        user = User(password_hash=hash_password("Password@123"), **ud)
        await user.insert()
        created_users.append(user)
        print(f"👤 Created user: {user.email} [{user.role}]")

    # Seed reports
    hazard_types = list(HazardType)
    severities   = list(SeverityLevel)
    statuses     = [ReportStatus.PENDING, ReportStatus.VERIFIED, ReportStatus.PENDING]

    citizens = [u for u in created_users if u.role == UserRole.CITIZEN]

    for i in range(30):
        lon, lat = random.choice(COASTAL_POINTS)
        lon += random.uniform(-0.5, 0.5)
        lat += random.uniform(-0.5, 0.5)
        reporter = random.choice(citizens)
        hazard    = random.choice(hazard_types)
        severity  = random.choice(severities)

        report = Report(
            hazard_type=hazard,
            title=f"Sample {hazard.value.replace('_', ' ').title()} report #{i+1}",
            description=f"Observed {hazard.value.replace('_', ' ')} near the coastline. Situation appears {severity.value}.",
            severity=severity,
            location={"type": "Point", "coordinates": [lon, lat]},
            location_name=f"Test Location {i+1}",
            state=random.choice(["Tamil Nadu", "Kerala", "Andhra Pradesh", "Odisha", "Maharashtra"]),
            reporter_id=str(reporter.id),
            reporter_name=reporter.name,
            status=random.choice(statuses),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
        )
        await report.insert()

    print(f"📋 Created 30 sample reports")
    print("\n✅ Seed complete!")
    print("\nLogin credentials (all passwords: Password@123):")
    for u in created_users:
        print(f"  {u.role.upper():<12} → {u.email}")


if __name__ == "__main__":
    asyncio.run(seed())
