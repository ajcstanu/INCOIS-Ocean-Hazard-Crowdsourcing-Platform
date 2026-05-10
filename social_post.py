from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


class SocialPost(Document):
    platform: SocialPlatform
    external_id: str                     # Platform-native post ID
    text: str
    author_handle: Optional[str] = None
    author_name: Optional[str] = None
    url: Optional[str] = None

    # NLP analysis
    is_hazard_related: bool = False
    hazard_types: List[str] = []
    urgency_score: float = 0.0
    sentiment_score: float = 0.0        # -1 (negative) to +1 (positive)
    language: str = "en"
    extracted_locations: List[str] = []
    extracted_entities: dict = {}

    # Geo (if detected)
    location: Optional[dict] = None

    # Linked report (if escalated)
    linked_report_id: Optional[str] = None
    linked_hotspot_id: Optional[str] = None

    # Engagement
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0

    posted_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "social_posts"
        indexes = [
            [("platform", 1), ("external_id", 1)],
            "is_hazard_related",
            "urgency_score",
            "collected_at",
        ]
