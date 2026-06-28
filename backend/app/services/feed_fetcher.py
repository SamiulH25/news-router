import asyncio
import hashlib
import logging
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session
from app.models.article import Article
from app.models.associations import FeedTopic, UserFeed
from app.models.feed import Feed
from app.models.topic import Topic
from app.models.user import User
from app.services.favicon import fetch_favicon_url
from app.services.entry_images import entry_image_url
from app.services.entry_quality import (
    clean_summary,
    clean_title,
    is_boilerplate_summary,
    is_valid_parsed_feed,
    should_ingest_entry,
)
from app.services.feed_discovery import discover_feed_from_site
from app.services.feed_repairs import repair_for_url
from app.services.feed_window import article_in_window, is_article_within_window
from app.services.matcher import match_article_to_topics
from app.services.rss_http import USER_AGENT
from app.services.section_feeds import resolve_poll_urls

logger = logging.getLogger(__name__)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _parse_published(entry: dict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                pass
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except (TypeError, ValueError):
                pass
    return None


def _entry_link(entry: dict) -> str | None:
    link = entry.get("link")
    if link:
        return link
    links = entry.get("links") or []
    for item in links:
        if item.get("href"):
            return item["href"]
    return None


async def _linked_topics(db: AsyncSession, feed: Feed) -> list[Topic]:
    """All topics any household member routes from this source (for polling section feeds)."""
    result = await db.execute(
        select(Topic)
        .join(FeedTopic, FeedTopic.topic_id == Topic.id)
        .where(FeedTopic.feed_id == feed.id)
        .distinct()
    )
    return list(result.scalars().all())


async def _ingest_parsed_feed(
    db: AsyncSession, feed: Feed, parsed: feedparser.FeedParserDict, source_url: str
) -> dict:
    if not is_valid_parsed_feed(parsed):
        logger.warning("Skipping ingest — %s is not a valid RSS/Atom feed", source_url)
        return {"entries_in_feed": 0, "new_articles": 0, "routed_to_topics": 0}

    entries_in_feed = len(parsed.entries)
    new_articles: list[Article] = []
    skipped = 0
    for entry in parsed.entries[:100]:
        link = _entry_link(entry)
        if not should_ingest_entry(entry, link):
            skipped += 1
            continue
        published_at = _parse_published(entry)
        if not is_article_within_window(published_at):
            continue
        title = clean_title(entry.get("title"), link)
        if not title:
            skipped += 1
            continue
        summary = clean_summary(entry.get("summary") or entry.get("description"), title=title)
        image_url = entry_image_url(entry, base_url=source_url)
        url_hash = _url_hash(link)
        existing = await db.execute(select(Article).where(Article.url == link))
        existing_article = existing.scalar_one_or_none()
        if existing_article:
            if image_url and not existing_article.image_url:
                existing_article.image_url = image_url
            if existing_article.summary and is_boilerplate_summary(existing_article.summary):
                existing_article.summary = summary
            if existing_article.title != title and is_boilerplate_summary(existing_article.title):
                existing_article.title = title
            continue
        article = Article(
            feed_id=feed.id,
            url=link,
            title=title,
            summary=summary,
            image_url=image_url,
            content_hash=url_hash,
            published_at=published_at,
        )
        db.add(article)
        new_articles.append(article)
    if skipped:
        logger.debug("Skipped %s low-quality entries from %s", skipped, source_url)
    await db.flush()
    routed = 0
    if new_articles:
        routed = await _route_new_articles(db, feed, new_articles, source_url=source_url)
    return {
        "entries_in_feed": entries_in_feed,
        "new_articles": len(new_articles),
        "routed_to_topics": routed,
    }


async def poll_all_feeds(db: AsyncSession, *, edition_user: User | None = None) -> dict:
    result = await db.execute(select(Feed))
    feeds = result.scalars().all()
    feed_results: list[dict] = []
    new_count = 0
    logger.info(
        "Starting feed poll for %s source(s) (concurrency=%s)",
        len(feeds),
        settings.feed_poll_concurrency,
    )

    if not feeds:
        feed_results = []
    else:
        sem = asyncio.Semaphore(max(1, settings.feed_poll_concurrency))

        async def poll_feed_worker(feed_id: int) -> dict:
            async with sem:
                return await _poll_feed_in_session(feed_id)

        outcomes = await asyncio.gather(
            *(poll_feed_worker(feed.id) for feed in feeds),
            return_exceptions=True,
        )
        for feed, outcome in zip(feeds, outcomes, strict=True):
            if isinstance(outcome, Exception):
                logger.exception("Failed to poll feed %s: %s", feed.url, outcome)
                feed.last_error = str(outcome)[:2000]
                feed.last_fetched_at = datetime.now(UTC)
                feed_results.append(
                    {
                        "feed_id": feed.id,
                        "feed_title": feed.title or feed.url,
                        "topics": [],
                        "poll_urls": [],
                        "new_articles": 0,
                        "routed_to_topics": 0,
                        "url_results": [],
                        "error": str(outcome)[:500],
                    }
                )
            else:
                feed_results.append(outcome)
                new_count += outcome["new_articles"]

    resurfaced = 0
    if edition_user:
        from app.services.feed_edition import resurface_user_edition

        resurfaced = await resurface_user_edition(db, edition_user)
        db_user = await db.get(User, edition_user.id)
        if db_user:
            db_user.last_edition_at = datetime.now(UTC)
        logger.info(
            "Built new edition for %s — %s stor%s in feed",
            edition_user.username,
            resurfaced,
            "y" if resurfaced == 1 else "ies",
        )
    await db.commit()
    logger.info("Feed poll complete: %s new article(s) from %s source(s)", new_count, len(feeds))
    return {
        "new_articles": new_count,
        "feeds": feed_results,
        "edition_stories": resurfaced if edition_user else None,
    }


async def _poll_feed_in_session(feed_id: int) -> dict:
    """Poll one source in its own DB session so feeds can run concurrently."""
    async with async_session() as session:
        feed = await session.get(Feed, feed_id)
        if not feed:
            raise ValueError(f"Feed {feed_id} not found")
        detail = await poll_single_feed(session, feed)
        await session.commit()
        return detail


async def _fetch_poll_url(
    client: httpx.AsyncClient, source_url: str
) -> tuple[str, feedparser.FeedParserDict | None, str | None]:
    try:
        response = await client.get(source_url)
        response.raise_for_status()
        return source_url, feedparser.parse(response.text), None
    except Exception as exc:
        return source_url, None, str(exc)[:500]


async def poll_single_feed(db: AsyncSession, feed: Feed) -> dict:
    feed.last_fetched_at = datetime.now(UTC)
    await _ensure_feed_rss_url(db, feed)
    linked = await _linked_topics(db, feed)
    topic_names = [t.name for t in linked]
    poll_urls = resolve_poll_urls(feed.url, feed.site_url, topic_names)

    logger.info(
        "Polling %r (id=%s) — topics=%s urls=%s",
        feed.title or feed.url,
        feed.id,
        topic_names or ["(none — using main feed only)"],
        poll_urls,
    )

    total_new = 0
    total_routed = 0
    url_results: list[dict] = []
    last_error: str | None = None

    async with httpx.AsyncClient(
        timeout=25.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        fetched = await asyncio.gather(
            *(_fetch_poll_url(client, source_url) for source_url in poll_urls)
        )
        for source_url, parsed, fetch_error in fetched:
            if fetch_error or parsed is None:
                logger.warning("Failed to poll %s for feed %s: %s", source_url, feed.id, fetch_error)
                last_error = fetch_error or "Empty feed response"
                url_results.append(
                    {
                        "url": source_url,
                        "entries_in_feed": 0,
                        "new_articles": 0,
                        "routed_to_topics": 0,
                        "error": last_error,
                    }
                )
                continue

            if source_url == feed.url or not feed.site_url:
                if not feed.title or feed.title == feed.url:
                    feed.title = parsed.feed.get("title") or feed.title
                if not feed.site_url:
                    feed.site_url = parsed.feed.get("link")
                if not feed.favicon_url and feed.site_url:
                    feed.favicon_url = await fetch_favicon_url(feed.site_url)
            ingest = await _ingest_parsed_feed(db, feed, parsed, source_url)
            total_new += ingest["new_articles"]
            total_routed += ingest["routed_to_topics"]
            url_results.append({"url": source_url, **ingest})
            logger.info(
                "  ↳ %s — %s entries, %s new, %s routed to topics",
                source_url,
                ingest["entries_in_feed"],
                ingest["new_articles"],
                ingest["routed_to_topics"],
            )

    if last_error and total_new == 0:
        feed.last_error = last_error
    else:
        feed.last_successful_fetch = datetime.now(UTC)
        feed.last_error = None

    if not topic_names:
        logger.warning(
            "  ⚠ %r has no topics linked — articles are fetched but not routed to your feed",
            feed.title or feed.url,
        )

    logger.info(
        "  ✓ %r done — %s new article(s), %s routed",
        feed.title or feed.url,
        total_new,
        total_routed,
    )

    return {
        "feed_id": feed.id,
        "feed_title": feed.title or feed.url,
        "topics": topic_names,
        "poll_urls": poll_urls,
        "new_articles": total_new,
        "routed_to_topics": total_routed,
        "url_results": url_results,
        "error": last_error,
    }


async def _eligible_topics_for_feed(db: AsyncSession, feed: Feed, user: User) -> list[Topic]:
    result = await db.execute(
        select(Topic)
        .join(FeedTopic, FeedTopic.topic_id == Topic.id)
        .where(
            FeedTopic.feed_id == feed.id,
            FeedTopic.user_id == user.id,
            Topic.user_id == user.id,
        )
    )
    return list(result.scalars().all())


async def _route_new_articles(
    db: AsyncSession, feed: Feed, articles: list[Article], *, source_url: str
) -> int:
    user_feeds = await db.execute(
        select(UserFeed).where(UserFeed.feed_id == feed.id).options(selectinload(UserFeed.user))
    )
    subscribers = [row.user for row in user_feeds.scalars().all()]
    routed = 0

    for user in subscribers:
        eligible_topics = await _eligible_topics_for_feed(db, feed, user)
        if not eligible_topics:
            continue
        for article in articles:
            routed += await match_article_to_topics(
                db, user, article, eligible_topics, feed_url=source_url, feed=feed
            )
    return routed


async def _ensure_feed_rss_url(db: AsyncSession, feed: Feed) -> None:
    """Repair feeds saved as a homepage URL, HTML 404, or retired RSS link."""
    repair = repair_for_url(feed.url)
    if repair:
        logger.info("Repaired legacy feed URL %r -> %r", feed.url, repair.url)
        feed.url = repair.url
        if repair.title:
            feed.title = repair.title
        if not feed.site_url:
            feed.site_url = repair.url

    try:
        async with httpx.AsyncClient(
            timeout=12.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(feed.url)
            response.raise_for_status()
            if is_valid_parsed_feed(feedparser.parse(response.text)):
                return
    except Exception:
        pass

    origin = feed.site_url or feed.url
    try:
        discovered = await discover_feed_from_site(origin)
    except Exception as exc:
        logger.warning("Could not repair feed URL for %s: %s", feed.url, exc)
        return

    repaired = discovered["feed_url"]
    if repaired != feed.url:
        logger.info("Repaired feed URL %r -> %r", feed.url, repaired)
        feed.url = repaired
        if not feed.site_url:
            feed.site_url = discovered.get("site_url")
        if discovered.get("title") and (not feed.title or feed.title == origin):
            feed.title = discovered["title"]


async def route_existing_feed_articles(db: AsyncSession, feed: Feed) -> int:
    """Re-match stored articles and fetch topic section feeds after routing changes."""
    try:
        detail = await poll_single_feed(db, feed)
        logger.info("Re-poll for feed %s: %s new", feed.id, detail["new_articles"])
    except Exception:
        logger.exception("Section re-poll failed for feed %s", feed.id)

    articles_result = await db.execute(
        select(Article)
        .where(Article.feed_id == feed.id, article_in_window())
        .order_by(Article.created_at.desc())
        .limit(100)
    )
    articles = articles_result.scalars().all()
    if not articles:
        return 0

    user_feeds = await db.execute(
        select(UserFeed).where(UserFeed.feed_id == feed.id).options(selectinload(UserFeed.user))
    )
    routed = 0
    for user_feed in user_feeds.scalars().all():
        eligible_topics = await _eligible_topics_for_feed(db, feed, user_feed.user)
        if not eligible_topics:
            continue
        for article in articles:
            routed += await match_article_to_topics(
                db, user_feed.user, article, eligible_topics, feed=feed
            )
    return routed
