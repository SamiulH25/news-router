import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session, get_db
from app.dependencies import get_current_user
from app.models.article import Article, UserArticle
from app.models.user import User
from app.schemas.digest import PollResponse
from app.services.feed_edition import archive_user_edition
from app.services.feed_fetcher import poll_all_feeds
from app.services.feed_window import user_article_in_window
from app.services.notifier import send_ntfy_notification
from app.services.user_schedule import is_user_digest_minute, user_local_now

router = APIRouter(prefix="/digest", tags=["digest"])
logger = logging.getLogger(__name__)


@router.post("/poll", response_model=PollResponse)
async def trigger_poll(user: User = Depends(get_current_user)):
    logger.info("Manual poll triggered by user %s", user.username)
    async with async_session() as db:
        archived = await archive_user_edition(db, user.id)
        logger.info("Archived %s stor%s from previous edition", archived, "y" if archived == 1 else "ies")
        result = await poll_all_feeds(db, edition_user=user)
    return PollResponse(**result)


@router.post("/notify-me")
async def notify_me(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    local = user_local_now(user)
    title = (
        "Your morning brief is ready"
        if local.hour < user.digest_evening_hour
        else "Your evening brief is ready"
    )
    sent = await _send_user_digest(db, user, title=title)
    return {"sent": sent}


async def send_daily_digests() -> int:
    now_utc = datetime.now(UTC).replace(second=0, microsecond=0)
    sent = 0
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for user in users:
            if not is_user_digest_minute(user, now_utc):
                continue
            local = user_local_now(user)
            title = (
                "Your morning brief is ready"
                if (local.hour, local.minute) == (user.digest_hour, user.digest_minute)
                else "Your evening brief is ready"
            )
            if await _send_user_digest(db, user, title=title):
                sent += 1
    return sent


async def _send_user_digest(db: AsyncSession, user: User, *, title: str) -> bool:
    window = user.feed_window_hours
    unread = await db.execute(
        select(func.count())
        .select_from(UserArticle)
        .join(Article)
        .where(
            UserArticle.user_id == user.id,
            UserArticle.is_read.is_(False),
            UserArticle.archived_at.is_(None),
            user_article_in_window(window),
        )
    )
    count = unread.scalar_one()
    if count == 0:
        return False

    headlines = await db.execute(
        select(Article.title)
        .join(UserArticle)
        .where(
            UserArticle.user_id == user.id,
            UserArticle.is_read.is_(False),
            UserArticle.archived_at.is_(None),
            user_article_in_window(window),
        )
        .order_by(UserArticle.surfaced_at.desc())
        .limit(3)
    )
    preview_titles = [row[0] for row in headlines.all()]
    topics = await db.execute(
        select(func.count(func.distinct(UserArticle.matched_topic_id)))
        .select_from(UserArticle)
        .join(Article)
        .where(
            UserArticle.user_id == user.id,
            UserArticle.is_read.is_(False),
            UserArticle.archived_at.is_(None),
            user_article_in_window(window),
        )
    )
    topic_count = topics.scalar_one()
    message = f"{count} new across {topic_count} topic{'s' if topic_count != 1 else ''}"
    if preview_titles:
        message += "\n• " + "\n• ".join(preview_titles)
    click = f"{settings.app_base_url.rstrip('/')}/feed"
    return await send_ntfy_notification(
        topic=user.ntfy_topic or "",
        title=title,
        message=message,
        click_url=click,
    )
