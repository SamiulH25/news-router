import asyncio
import time

import pytest

from app.services import feed_fetcher


@pytest.mark.asyncio
async def test_poll_all_feeds_runs_sources_concurrently(monkeypatch):
    delays: dict[int, float] = {1: 0.12, 2: 0.12, 3: 0.12}
    started: list[float] = []

    class FakeFeed:
        def __init__(self, feed_id: int):
            self.id = feed_id
            self.url = f"https://example.com/{feed_id}"
            self.title = f"Feed {feed_id}"
            self.last_error = None
            self.last_fetched_at = None

    feeds = [FakeFeed(1), FakeFeed(2), FakeFeed(3)]

    async def fake_execute(_query):
        class Result:
            def scalars(self):
                class Scalars:
                    def all(self_inner):
                        return feeds

                return Scalars()

        return Result()

    async def fake_poll_feed_in_session(feed_id: int):
        started.append(time.perf_counter())
        await asyncio.sleep(delays[feed_id])
        return {
            "feed_id": feed_id,
            "feed_title": f"Feed {feed_id}",
            "topics": [],
            "poll_urls": [],
            "new_articles": 1,
            "routed_to_topics": 1,
            "url_results": [],
            "error": None,
        }

    class FakeSession:
        async def execute(self, query):
            return await fake_execute(query)

        async def commit(self):
            return None

    monkeypatch.setattr(feed_fetcher.settings, "feed_poll_concurrency", 3)
    monkeypatch.setattr(feed_fetcher, "_poll_feed_in_session", fake_poll_feed_in_session)

    result = await feed_fetcher.poll_all_feeds(FakeSession(), edition_user=None)

    assert result["new_articles"] == 3
    assert len(result["feeds"]) == 3
    assert len(started) == 3
    # Sequential would take ~0.36s; parallel with concurrency 3 should finish closer to ~0.12s.
    span = max(started) - min(started)
    assert span < 0.08
