import random
from datetime import UTC, datetime

from app.models.article import Article, UserArticle
from app.services.preference_learning import affinity_score
from app.services.story_cluster import cluster_key


def _freshness_score(article: Article, surfaced_at: datetime, window_hours: int) -> float:
    anchor = article.published_at or surfaced_at
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=UTC)
    hours_old = max(0.0, (datetime.now(UTC) - anchor).total_seconds() / 3600)
    return max(0.0, 1.0 - hours_old / max(window_hours, 1))


def _base_score(
    row: UserArticle,
    profile: dict[str, dict[str, float]],
    *,
    window_hours: int,
) -> float:
    article = row.article
    taste = affinity_score(
        profile,
        topic_id=row.matched_topic_id,
        feed_id=article.feed_id,
        title=article.title,
    )
    fresh = _freshness_score(article, row.surfaced_at, window_hours)
    unread = 0.35 if not row.is_read else 0.0
    open_boost = 0.2 if row.opened_full else 0.0
    less_penalty = -0.35 if row.skipped else 0.0

    exploration = random.uniform(0, 0.08)
    return taste + fresh * 0.9 + unread + open_boost + less_penalty + exploration


def rank_timeline(
    rows: list[UserArticle],
    profile: dict[str, dict[str, float]],
    *,
    window_hours: int,
) -> list[UserArticle]:
    """Greedy ranked feed with topic/cluster diversity (TikTok-style interleaving)."""
    if not rows:
        return []

    pool = list(rows)
    ranked: list[UserArticle] = []
    recent_topics: list[int] = []
    recent_clusters: list[str] = []

    while pool:
        best_idx = 0
        best_score = float("-inf")
        for i, row in enumerate(pool):
            score = _base_score(row, profile, window_hours=window_hours)
            topic_id = row.matched_topic_id
            cluster = cluster_key(row.article.title)

            if recent_topics.count(topic_id) >= 2:
                score -= 0.45
            if cluster in recent_clusters[-3:]:
                score -= 0.35
            if topic_id not in recent_topics[-4:]:
                score += 0.12

            if score > best_score:
                best_score = score
                best_idx = i

        pick = pool.pop(best_idx)
        ranked.append(pick)
        recent_topics.append(pick.matched_topic_id)
        recent_clusters.append(cluster_key(pick.article.title))
        if len(recent_topics) > 6:
            recent_topics.pop(0)

    return ranked


def rank_within_groups(
    rows: list[UserArticle],
    profile: dict[str, dict[str, float]],
    *,
    window_hours: int,
) -> list[UserArticle]:
    """Chronological fallback with light re-ranking inside topic buckets."""
    by_topic: dict[int, list[UserArticle]] = {}
    for row in rows:
        by_topic.setdefault(row.matched_topic_id, []).append(row)

    topic_order = sorted(
        by_topic.keys(),
        key=lambda tid: profile.get("topic", {}).get(str(tid), 0.0),
        reverse=True,
    )

    ordered: list[UserArticle] = []
    for tid in topic_order:
        bucket = by_topic[tid]
        bucket.sort(
            key=lambda r: _base_score(r, profile, window_hours=window_hours),
            reverse=True,
        )
        ordered.extend(bucket)
    return ordered
