import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from config.settings import settings
from loguru import logger
import uuid

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

ALLOWED_TYPES = (
    settings.allowed_image_types_list + settings.allowed_video_types_list
)


async def validate_and_upload(file: UploadFile, folder: str = "incois/reports") -> dict:
    """Validate file and upload to Cloudinary. Returns {url, media_type, public_id}."""

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed.",
        )

    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit.",
        )

    resource_type = "video" if file.content_type in settings.allowed_video_types_list else "image"
    public_id = f"{folder}/{uuid.uuid4().hex}"

    try:
        result = cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            resource_type=resource_type,
            folder=folder,
        )
        return {
            "url": result["secure_url"],
            "media_type": resource_type,
            "public_id": result["public_id"],
        }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Media upload failed. Please try again.",
        )


async def delete_media(public_id: str, resource_type: str = "image") -> None:
    """Delete a Cloudinary asset."""
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception as e:
        logger.warning(f"Cloudinary delete failed for {public_id}: {e}")
