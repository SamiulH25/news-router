import re
from datetime import UTC, datetime
from html import unescape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, UserArticle
from app.models.feed import Feed
from app.models.topic import Topic
from app.models.user import User
from app.services.section_feeds import (
    feed_section_from_url,
    section_feed_for_topic,
    topic_matches_feed_section,
)


def _parse_keywords(keywords: str) -> list[str]:
    return [k.strip().lower() for k in keywords.replace("\n", ",").split(",") if k.strip()]


def _strip_html(text: str) -> str:
    plain = re.sub(r"<[^>]+>", " ", text)
    return unescape(re.sub(r"\s+", " ", plain)).strip()


def _article_haystack(article: Article) -> str:
    summary = _strip_html(article.summary or "")
    return f"{article.title} {summary}".lower()


def _keyword_matches(haystack: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if " " in keyword:
        return keyword in haystack
    if len(keyword) <= 4:
        return bool(re.search(rf"\b{re.escape(keyword)}\b", haystack))
    return keyword in haystack


def article_matches_topic(article: Article, topic: Topic, feed_url: str | None = None) -> bool:
    section = feed_section_from_url(feed_url)
    if section and topic_matches_feed_section(topic.name, section):
        pass
    else:
        keywords = _parse_keywords(topic.keywords)
        if not keywords:
            return True
        haystack = _article_haystack(article)
        if not any(_keyword_matches(haystack, keyword) for keyword in keywords):
            return False

    excludes = _parse_keywords(topic.exclude_keywords)
    if excludes:
        haystack = _article_haystack(article)
        if any(_keyword_matches(haystack, word) for word in excludes):
            return False
    return True


def _source_url_for_topic(feed: Feed | None, topic: Topic, fallback_url: str | None) -> str | None:
    if feed:
        return section_feed_for_topic(feed.site_url, feed.url, topic.name) or feed.url
    return fallback_url


async def match_article_to_topics(
    db: AsyncSession,
    user: User,
    article: Article,
    topics: list[Topic],
    *,
    feed_url: str | None = None,
    feed: Feed | None = None,
) -> int:
    matched = 0
    for topic in topics:
        source_url = _source_url_for_topic(feed, topic, feed_url)
        if not article_matches_topic(article, topic, source_url):
            continue
        existing = await db.execute(
            select(UserArticle).where(
                UserArticle.user_id == user.id,
                UserArticle.article_id == article.id,
                UserArticle.matched_topic_id == topic.id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            if row.archived_at is not None:
                row.archived_at = None
                row.surfaced_at = datetime.now(UTC)
                row.is_read = False
                matched += 1
            continue
        db.add(
            UserArticle(
                user_id=user.id,
                article_id=article.id,
                matched_topic_id=topic.id,
                is_read=False,
            )
        )
        matched += 1
    return matched
