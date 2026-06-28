from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.feed_ranker import rank_timeline
from app.services.preference_learning import affinity_score


def test_affinity_score_favors_learned_topic():
    profile = {"topic": {"1": 0.8, "2": -0.2}, "feed": {}, "keyword": {}}
    high = affinity_score(profile, topic_id=1, feed_id=5, title="Local council vote")
    low = affinity_score(profile, topic_id=2, feed_id=5, title="Local council vote")
    assert high > low


def test_rank_timeline_puts_preferred_topic_first():
    profile = {"topic": {"10": 0.9, "20": -0.4}, "feed": {}, "keyword": {}}
    now = datetime.now(UTC)

    def row(topic_id: int, title: str) -> SimpleNamespace:
        return SimpleNamespace(
            id=topic_id,
            user_id=1,
            matched_topic_id=topic_id,
            is_read=False,
            skipped=False,
            opened_full=False,
            dwell_ms=0,
            surfaced_at=now,
            article=SimpleNamespace(
                id=topic_id,
                feed_id=1,
                title=title,
                published_at=now,
            ),
        )

    rows = [
        row(20, "Sports team wins championship game tonight"),
        row(10, "Election results shift parliament balance"),
        row(20, "Trade deadline moves shake roster"),
    ]
    ranked = rank_timeline(rows, profile, window_hours=12)
    assert ranked[0].matched_topic_id == 10
