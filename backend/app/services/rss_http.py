from urllib.parse import urlparse

import feedparser
import httpx

USER_AGENT = "NewsRouter/1.0 (compatible; RSS reader)"


async def fetch_feed_metadata(url: str) -> dict:
    async with httpx.AsyncClient(
        timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        parsed = feedparser.parse(response.text)
    title = parsed.feed.get("title") or urlparse(url).netloc or url
    site_url = parsed.feed.get("link")
    return {"title": title, "site_url": site_url}
