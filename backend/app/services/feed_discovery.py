import asyncio
import logging
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import feedparser
import httpx

from app.services.rss_http import USER_AGENT, fetch_feed_metadata
from app.services.section_feeds import (
    known_feed_candidates,
    list_sections_for_site,
    path_section_feed_candidates,
)

logger = logging.getLogger(__name__)

PROBE_TIMEOUT = 8.0
HTML_TIMEOUT = 12.0

FEED_TYPES = (
    "application/rss+xml",
    "application/atom+xml",
    "application/rdf+xml",
    "application/xml",
    "text/xml",
)

COMMON_FEED_PATHS = (
    "/feed",
    "/feed/",
    "/rss",
    "/rss.xml",
    "/rss/",
    "/news/rss.xml",
    "/atom.xml",
    "/index.xml",
    "/feeds/posts/default",
    "/blog/feed",
    "/?feed=rss2",
    "/.rss",
)


class _FeedLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        rel = attr_map.get("rel", "").lower()
        typ = attr_map.get("type", "").lower()
        href = attr_map.get("href", "").strip()
        if "alternate" in rel.split() and typ in FEED_TYPES and href:
            self.links.append(urljoin(self.base_url, href))


def normalize_site_url(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("URL is required")
    if not re.match(r"^https?://", value, re.I):
        value = f"https://{value}"
    parsed = urlparse(value)
    if not parsed.netloc:
        raise ValueError("Invalid website URL")
    return value


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _domain_title(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    part = host.split(".")[0]
    return part.replace("-", " ").title() if part else host


def _extract_html_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I | re.S)
    if match:
        title = re.sub(r"\s+", " ", match.group(1)).strip()
        if title:
            return title[:200]
    og = re.search(
        r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if og:
        return og.group(1).strip()[:200]
    og2 = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']',
        html,
        re.I,
    )
    if og2:
        return og2.group(1).strip()[:200]
    return None


def _unique(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


async def _is_valid_feed(url: str) -> bool:
    try:
        async with httpx.AsyncClient(
            timeout=PROBE_TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            parsed = feedparser.parse(response.text)
        if parsed.bozo and not parsed.entries and not parsed.feed.get("title"):
            return False
        return bool(parsed.entries or parsed.feed.get("title"))
    except Exception:
        return False


async def _fetch_text(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(
        timeout=HTML_TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text, str(response.url)


async def _first_valid_feed(urls: list[str]) -> str | None:
    """Probe candidate feed URLs in parallel; return the first that validates."""
    ordered = _unique(urls)
    if not ordered:
        return None

    async def probe(url: str) -> str | None:
        return url if await _is_valid_feed(url) else None

    results = await asyncio.gather(*(probe(url) for url in ordered), return_exceptions=True)
    for result in results:
        if isinstance(result, str):
            return result
    return None


async def _build_discovery_result(
    feed_url: str, *, source: str, fallback_title: str, fallback_site: str
) -> dict:
    meta = await fetch_feed_metadata(feed_url)
    site_url = meta.get("site_url") or fallback_site
    return {
        "feed_url": feed_url,
        "title": meta.get("title") or fallback_title,
        "site_url": site_url,
        "source": source,
        "sections": list_sections_for_site(site_url, feed_url),
    }


async def discover_feed_from_site(user_input: str) -> dict:
    """
    Given a homepage or feed URL, return the site's main RSS feed.
    Section feeds are resolved automatically when topics are linked.
    """
    normalized = normalize_site_url(user_input)
    origin = _origin(normalized)
    fallback_title = _domain_title(normalized)

    if await _is_valid_feed(normalized):
        return await _build_discovery_result(
            normalized, source="direct", fallback_title=fallback_title, fallback_site=origin
        )

    section_hit = await _first_valid_feed(path_section_feed_candidates(normalized))
    if section_hit:
        return await _build_discovery_result(
            section_hit, source="section", fallback_title=fallback_title, fallback_site=origin
        )

    # Known feeds and common paths before fetching HTML (some sites block or stall scrapers).
    quick_candidates: list[str] = []
    quick_candidates.extend(known_feed_candidates(origin))
    quick_candidates.extend(urljoin(origin, path) for path in COMMON_FEED_PATHS)
    quick_hit = await _first_valid_feed(quick_candidates)
    if quick_hit:
        return await _build_discovery_result(
            quick_hit, source="known", fallback_title=fallback_title, fallback_site=origin
        )

    try:
        html, page_url = await _fetch_text(normalized)
    except Exception as exc:
        logger.warning("HTML fetch failed for %s: %s", normalized, exc)
        raise ValueError(
            f"Could not reach {urlparse(origin).netloc.removeprefix('www.')}. "
            "Check the URL or paste a direct RSS link."
        ) from exc

    page_origin = _origin(page_url)
    page_title = _extract_html_title(html) or fallback_title

    parser = _FeedLinkParser(page_url)
    try:
        parser.feed(html)
    except Exception:
        logger.debug("HTML parse failed for %s", page_url)

    scraped_candidates: list[str] = []
    scraped_candidates.extend(path_section_feed_candidates(normalized))
    scraped_candidates.extend(path_section_feed_candidates(page_url))
    scraped_candidates.extend(known_feed_candidates(page_origin))
    scraped_candidates.extend(parser.links)
    scraped_candidates.extend(urljoin(page_origin, path) for path in COMMON_FEED_PATHS)

    scraped_hit = await _first_valid_feed(scraped_candidates)
    if scraped_hit:
        return await _build_discovery_result(
            scraped_hit, source="discovered", fallback_title=page_title, fallback_site=page_origin
        )

    domain = urlparse(page_origin).netloc.removeprefix("www.")
    raise ValueError(
        f"Could not find an RSS feed for {domain}. Try a different news site or paste a direct RSS link."
    )
