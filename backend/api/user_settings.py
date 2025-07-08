from fastapi import APIRouter, HTTPException, Depends
from services.user_service import user_service
from services.security import security_service
from models.auth import UserSettings, UserSettingsUpdate
import logging

logger = logging.getLogger(__name__)

settings_router = APIRouter(prefix="/settings", tags=["User Settings"])


@settings_router.get("/", response_model=UserSettings)
async def get_user_settings(user_id: str = Depends(security_service.get_current_user_id)):
    try:
        settings = await user_service.get_user_settings(user_id)
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@settings_router.patch("/", response_model=UserSettings)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    user_id: str = Depends(security_service.get_current_user_id),
):
    try:
        settings = await user_service.update_user_settings(
            user_id,
            preferred_language=settings_update.preferred_language,
            show_explanation=settings_update.show_explanation,
            show_sql=settings_update.show_sql,
        )
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")

