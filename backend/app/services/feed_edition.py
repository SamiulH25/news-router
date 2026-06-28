from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, UserArticle
from app.models.associations import UserFeed
from app.models.feed import Feed
from app.models.user import User
from app.services.feed_fetcher import _eligible_topics_for_feed
from app.services.feed_window import article_in_window
from app.services.matcher import match_article_to_topics


async def archive_user_edition(db: AsyncSession, user_id: int) -> int:
    """Move the user's current feed items into the archive."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(UserArticle)
        .where(UserArticle.user_id == user_id, UserArticle.archived_at.is_(None))
        .values(archived_at=now)
    )
    return result.rowcount or 0


async def resurface_user_edition(db: AsyncSession, user: User) -> int:
    """Rebuild the active feed from in-window articles on the user's subscribed sources."""
    window = user.feed_window_hours
    feeds_result = await db.execute(
        select(Feed)
        .join(UserFeed, UserFeed.feed_id == Feed.id)
        .where(UserFeed.user_id == user.id)
    )
    feeds = feeds_result.scalars().all()
    surfaced = 0
    for feed in feeds:
        eligible = await _eligible_topics_for_feed(db, feed, user)
        if not eligible:
            continue
        articles_result = await db.execute(
            select(Article).where(Article.feed_id == feed.id, article_in_window(window))
        )
        for article in articles_result.scalars().all():
            surfaced += await match_article_to_topics(
                db, user, article, eligible, feed_url=feed.url, feed=feed
            )
    return surfaced


async def load_archived_feed(db: AsyncSession, user: User, *, limit: int = 200) -> list[UserArticle]:
    result = await db.execute(
        select(UserArticle)
        .join(Article)
        .where(UserArticle.user_id == user.id, UserArticle.archived_at.isnot(None))
        .options(
            selectinload(UserArticle.article).selectinload(Article.feed),
            selectinload(UserArticle.matched_topic),
        )
        .order_by(UserArticle.archived_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
