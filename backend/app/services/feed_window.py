from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.sql import ColumnElement

from app.config import settings
from app.models.article import Article, UserArticle


def feed_window_since(hours: int | None = None) -> datetime:
    window = hours if hours is not None else settings.feed_window_hours
    return datetime.now(UTC) - timedelta(hours=window)


def user_article_in_window(hours: int | None = None) -> ColumnElement:
    """Articles published within the window, or surfaced recently if no publish date."""
    since = feed_window_since(hours)
    return or_(
        and_(Article.published_at.isnot(None), Article.published_at >= since),
        and_(Article.published_at.is_(None), UserArticle.surfaced_at >= since),
    )


def article_in_window(hours: int | None = None) -> ColumnElement:
    """SQL filter for articles published (or ingested) within the feed window."""
    since = feed_window_since(hours)
    return or_(
        and_(Article.published_at.isnot(None), Article.published_at >= since),
        and_(Article.published_at.is_(None), Article.created_at >= since),
    )


def is_article_within_window(published_at: datetime | None, surfaced_at: datetime | None = None) -> bool:
    since = feed_window_since()
    if published_at is not None:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)
        return published_at >= since
    if surfaced_at is not None:
        if surfaced_at.tzinfo is None:
            surfaced_at = surfaced_at.replace(tzinfo=UTC)
        return surfaced_at >= since
    return True
