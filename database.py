from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger
from config.settings import settings

# Import all document models here
from app.models.user import User
from app.models.report import Report
from app.models.hotspot import Hotspot
from app.models.social_post import SocialPost

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global _client
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=45000,
        )
        # Ping to verify connection
        await _client.admin.command("ping")

        db_name = settings.MONGODB_URI.split("/")[-1].split("?")[0]
        database = _client[db_name]

        await init_beanie(
            database=database,
            document_models=[User, Report, Hotspot, SocialPost],
        )
        logger.info("✅ MongoDB connected and Beanie initialized")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def disconnect_db() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_client() -> AsyncIOMotorClient | None:
    return _client
