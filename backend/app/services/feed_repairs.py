"""Map broken or retired feed URLs to working replacements."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeedRepair:
    url: str
    title: str | None = None


def _normalize_feed_url(url: str) -> str:
    return url.rstrip("/")


# Keys are normalized (no trailing slash).
LEGACY_FEED_REPAIRS: dict[str, FeedRepair] = {
    _normalize_feed_url("https://www.ctvnews.ca/rss/ctvnews-ca-top-stories"): FeedRepair(
        url="https://globalnews.ca/feed/",
        title="Global News",
    ),
    _normalize_feed_url("https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009"): FeedRepair(
        url="https://globalnews.ca/feed/",
        title="Global News",
    ),
    _normalize_feed_url("https://www.thedailystar.net/feed"): FeedRepair(
        url="https://www.thedailystar.net/rss.xml",
        title="The Daily Star",
    ),
}


def repair_for_url(feed_url: str) -> FeedRepair | None:
    return LEGACY_FEED_REPAIRS.get(_normalize_feed_url(feed_url))
