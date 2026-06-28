from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.auth import generate_ntfy_topic

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    digest_hour: int | None = Field(default=None, ge=0, le=23)
    digest_minute: int | None = Field(default=None, ge=0, le=59)
    digest_evening_hour: int | None = Field(default=None, ge=0, le=23)
    digest_evening_minute: int | None = Field(default=None, ge=0, le=59)
    timezone: str | None = None
    feed_window_hours: int | None = Field(default=None, ge=1, le=72)
    onboarded: bool | None = None
    personalized_feed: bool | None = None
    regenerate_ntfy_topic: bool = False


@router.patch("", response_model=UserResponse)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.digest_hour is not None:
        user.digest_hour = body.digest_hour
    if body.digest_minute is not None:
        user.digest_minute = body.digest_minute
    if body.digest_evening_hour is not None:
        user.digest_evening_hour = body.digest_evening_hour
    if body.digest_evening_minute is not None:
        user.digest_evening_minute = body.digest_evening_minute
    if body.timezone is not None:
        user.timezone = body.timezone.strip() or "UTC"
    if body.feed_window_hours is not None:
        user.feed_window_hours = body.feed_window_hours
    if body.onboarded is not None:
        user.onboarded = body.onboarded
    if body.personalized_feed is not None:
        user.personalized_feed = body.personalized_feed
    if body.regenerate_ntfy_topic:
        user.ntfy_topic = generate_ntfy_topic()
    await db.commit()
    await db.refresh(user)
    return user
