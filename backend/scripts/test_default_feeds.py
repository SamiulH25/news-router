import asyncio

import feedparser
import httpx

from app.data.default_feeds import DEFAULT_NEWS_OUTLETS
from app.services.entry_quality import is_valid_parsed_feed
from app.services.rss_http import USER_AGENT

ALT_FEEDS = [
    ("CTV alt 1", "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories"),
    ("CTV alt 2", "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories.rss"),
    ("CTV alt 3", "https://www.ctvnews.ca/rss/TopStories"),
    ("CTV alt 4", "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories.xml"),
    ("Daily Star alt 1", "https://www.thedailystar.net/feed"),
    ("Daily Star alt 2", "https://www.thedailystar.net/rss.xml"),
    ("Daily Star alt 3", "https://www.thedailystar.net/feed/rss.xml"),
    ("Daily Star alt 4", "https://www.thedailystar.net/rss"),
    ("Prothom Alo EN", "https://en.prothomalo.com/feed"),
    ("Dhaka Tribune", "https://www.dhakatribune.com/feed/"),
    ("Global News", "https://globalnews.ca/feed/"),
]


async def probe(url: str, title: str) -> None:
    print(f"=== {title} ===")
    print(f"URL: {url}")
    try:
        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(url)
            ctype = response.headers.get("content-type", "?")
            print(f"Status: {response.status_code} -> {response.url}")
            print(f"Content-Type: {ctype}")
            print(f"Body len: {len(response.text)}")
            print(f"Start: {response.text[:150]!r}")
            parsed = feedparser.parse(response.text)
            valid = is_valid_parsed_feed(parsed)
            print(f"Title: {parsed.feed.get('title')!r}, entries: {len(parsed.entries)}, valid: {valid}")
            if parsed.bozo_exception:
                print(f"Bozo: {parsed.bozo_exception}")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
    print()


async def main() -> None:
    for outlet in DEFAULT_NEWS_OUTLETS:
        await probe(outlet.url, outlet.title)
    print("--- alternatives ---")
    for title, url in ALT_FEEDS:
        await probe(url, title)


if __name__ == "__main__":
    asyncio.run(main())
