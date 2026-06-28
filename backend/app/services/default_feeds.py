import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.default_feeds import DefaultOutlet, resolve_outlets
from app.models.feed import Feed
from app.models.user import User
from app.services.feed_subscribe import subscribe_user_to_feed

logger = logging.getLogger(__name__)


async def seed_outlets(
    db: AsyncSession,
    user: User,
    topic_id: int,
    outlet_urls: list[str],
) -> list[Feed]:
    outlets = resolve_outlets(outlet_urls)
    feeds: list[Feed] = []
    for outlet in outlets:
        feed = await _subscribe_outlet(db, user, topic_id, outlet)
        if feed is not None:
            feeds.append(feed)
    return feeds


async def seed_default_feeds(db: AsyncSession, user: User, topic_id: int) -> list[Feed]:
    from app.data.default_feeds import default_selected_urls

    return await seed_outlets(db, user, topic_id, default_selected_urls())


async def _subscribe_outlet(
    db: AsyncSession,
    user: User,
    topic_id: int,
    outlet: DefaultOutlet,
) -> Feed | None:
    try:
        return await subscribe_user_to_feed(
            db,
            user,
            url=outlet.url,
            title=outlet.title,
            topic_ids=[topic_id],
        )
    except Exception as exc:
        logger.warning("Failed to seed outlet %s: %s", outlet.title, exc)
        return None
