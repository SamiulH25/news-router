import math
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affinity import UserAffinity
from app.models.article import UserArticle

EMA_ALPHA = 0.18

# Only intentional actions — never inferred from scroll speed or time on card.
EVENT_SIGNALS = {
    "open": 0.85,
    "less": -0.55,
}

_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "from",
    "this",
    "will",
    "have",
    "has",
    "are",
    "was",
    "were",
    "its",
    "after",
    "over",
    "into",
    "about",
    "says",
    "new",
}


def title_keywords(title: str) -> list[str]:
    plain = re.sub(r"[^\w\s]", " ", title.lower())
    return [w for w in plain.split() if len(w) > 2 and w not in _STOPWORDS][:12]


async def _get_or_create_affinity(
    db: AsyncSession, user_id: int, kind: str, key: str
) -> UserAffinity:
    result = await db.execute(
        select(UserAffinity).where(
            UserAffinity.user_id == user_id,
            UserAffinity.kind == kind,
            UserAffinity.key == key,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    row = UserAffinity(user_id=user_id, kind=kind, key=key, weight=0.0)
    db.add(row)
    await db.flush()
    return row


async def _bump_affinity(db: AsyncSession, user_id: int, kind: str, key: str, signal: float) -> None:
    if not key or signal == 0:
        return
    row = await _get_or_create_affinity(db, user_id, kind, key)
    row.weight = max(-1.0, min(1.0, row.weight * (1 - EMA_ALPHA) + signal * EMA_ALPHA))
    row.updated_at = datetime.now(UTC)


async def load_affinity_map(db: AsyncSession, user_id: int) -> dict[str, dict[str, float]]:
    result = await db.execute(select(UserAffinity).where(UserAffinity.user_id == user_id))
    profile: dict[str, dict[str, float]] = {"topic": {}, "feed": {}, "keyword": {}}
    for row in result.scalars().all():
        profile.setdefault(row.kind, {})[row.key] = row.weight
    return profile


async def record_engagement(
    db: AsyncSession,
    user_article: UserArticle,
    *,
    event: str,
) -> None:
    signal = EVENT_SIGNALS.get(event)
    if signal is None:
        return

    article = user_article.article
    if event == "open":
        user_article.opened_full = True
    elif event == "less":
        user_article.skipped = True

    topic_key = str(user_article.matched_topic_id)
    feed_key = str(article.feed_id)

    await _bump_affinity(db, user_article.user_id, "topic", topic_key, signal)
    await _bump_affinity(db, user_article.user_id, "feed", feed_key, signal * 0.7)

    keyword_signal = signal * 0.35 if signal > 0 else signal * 0.5
    for word in title_keywords(article.title):
        await _bump_affinity(db, user_article.user_id, "keyword", word, keyword_signal)


def affinity_score(
    profile: dict[str, dict[str, float]],
    *,
    topic_id: int,
    feed_id: int,
    title: str,
) -> float:
    topics = profile.get("topic", {})
    feeds = profile.get("feed", {})
    keywords = profile.get("keyword", {})

    topic_w = topics.get(str(topic_id), 0.0)
    feed_w = feeds.get(str(feed_id), 0.0)
    words = title_keywords(title)
    keyword_w = sum(keywords.get(w, 0.0) for w in words) / max(len(words), 1)

    raw = topic_w * 3.2 + feed_w * 1.6 + keyword_w * 2.4
    return math.tanh(raw)
