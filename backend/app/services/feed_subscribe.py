import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.associations import FeedTopic, UserFeed
from app.models.feed import Feed
from app.models.topic import Topic
from app.models.user import User
from app.services.feed_discovery import discover_feed_from_site
from app.services.favicon import fetch_favicon_url
from app.services.feed_fetcher import poll_single_feed, route_existing_feed_articles

logger = logging.getLogger(__name__)


async def subscribe_user_to_feed(
    db: AsyncSession,
    user: User,
    *,
    url: str,
    title: str | None = None,
    topic_ids: list[int] | None = None,
    poll: bool = True,
    route: bool = True,
) -> Feed:
    discovered = await discover_feed_from_site(url)
    feed_url = discovered["feed_url"]
    site_url = discovered.get("site_url")
    feed_title = title or discovered["title"] or feed_url

    existing = await db.execute(select(Feed).where(Feed.url == feed_url))
    feed = existing.scalar_one_or_none()
    if not feed:
        favicon = await fetch_favicon_url(site_url) if site_url else None
        feed = Feed(url=feed_url, title=feed_title, site_url=site_url, favicon_url=favicon)
        db.add(feed)
        await db.flush()
    elif title:
        feed.title = title

    sub = await db.execute(select(UserFeed).where(UserFeed.user_id == user.id, UserFeed.feed_id == feed.id))
    if not sub.scalar_one_or_none():
        db.add(UserFeed(user_id=user.id, feed_id=feed.id))

    resolved_topic_ids = list(topic_ids or [])
    if not resolved_topic_ids:
        resolved_topic_ids = await _default_topic_ids(db, user)

    if resolved_topic_ids:
        await set_feed_topics(db, user, feed.id, resolved_topic_ids)

    if poll:
        try:
            await poll_single_feed(db, feed)
        except Exception as exc:
            logger.warning("Initial poll failed for feed %s: %s", feed.id, exc)

    if route and resolved_topic_ids:
        await route_existing_feed_articles(db, feed)

    return feed


async def _default_topic_ids(db: AsyncSession, user: User) -> list[int]:
    result = await db.execute(select(Topic).where(Topic.user_id == user.id).order_by(Topic.name))
    topics = result.scalars().all()
    if topics:
        return []
    topic = Topic(user_id=user.id, name="General", keywords="")
    db.add(topic)
    await db.flush()
    return [topic.id]


async def set_feed_topics(db: AsyncSession, user: User, feed_id: int, topic_ids: list[int]) -> None:
    owned = await db.execute(select(Topic.id).where(Topic.user_id == user.id, Topic.id.in_(topic_ids)))
    allowed = set(owned.scalars().all())
    if len(allowed) != len(set(topic_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid topic selection")
    sub = await db.execute(select(UserFeed).where(UserFeed.user_id == user.id, UserFeed.feed_id == feed_id))
    if not sub.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscribe to feed first")
    existing = await db.execute(
        select(FeedTopic).where(
            FeedTopic.feed_id == feed_id,
            FeedTopic.user_id == user.id,
            FeedTopic.topic_id.in_(topic_ids),
        )
    )
    existing_ids = {row.topic_id for row in existing.scalars().all()}
    for topic_id in topic_ids:
        if topic_id not in existing_ids:
            db.add(FeedTopic(user_id=user.id, feed_id=feed_id, topic_id=topic_id))
    all_links = await db.execute(
        select(FeedTopic).where(FeedTopic.feed_id == feed_id, FeedTopic.user_id == user.id)
    )
    for link in all_links.scalars().all():
        if link.topic_id not in set(topic_ids):
            await db.delete(link)
