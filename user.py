from beanie import Document, Indexed
from pydantic import EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "citizen"
    OFFICIAL = "official"
    ANALYST = "analyst"
    ADMIN = "admin"


class UserLanguage(str, Enum):
    EN = "en"
    HI = "hi"
    TA = "ta"
    TE = "te"
    ML = "ml"
    KN = "kn"
    BN = "bn"
    OR = "or"


class User(Document):
    name: str = Field(..., min_length=2, max_length=100)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    role: UserRole = UserRole.CITIZEN
    language: UserLanguage = UserLanguage.EN
    phone: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None
    refresh_token: Optional[str] = None

    # Location (for citizen reporters)
    location: Optional[dict] = None   # {state, district, coordinates}

    # Stats
    reports_count: int = 0
    verified_reports_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            "email",
            "role",
            "is_active",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ravi Kumar",
                "email": "ravi@example.com",
                "role": "citizen",
                "language": "hi",
            }
        }
