import logging
import re
from urllib.parse import urlparse

import feedparser
import httpx

from app.services.rss_http import USER_AGENT

logger = logging.getLogger(__name__)

# Topic display names that map to a site's RSS section slug.
SECTION_TOPIC_ALIASES: dict[str, set[str]] = {
    "politics": {"politics", "government", "political"},
    "technology": {"technology", "tech"},
    "business": {"business", "finance", "economy"},
    "science": {"science"},
    "science_and_environment": {"science", "environment", "climate"},
    "health": {"health"},
    "sport": {"sport", "sports"},
    "world": {"world", "international"},
    "uk": {"uk", "britain", "british"},
    "uk-news": {"uk", "britain", "british"},
    "entertainment": {"entertainment", "arts", "culture"},
    "entertainment_and_arts": {"entertainment", "arts", "culture"},
    "canada": {"canada", "canadian"},
}

FEED_SECTION_SEGMENTS = frozenset(SECTION_TOPIC_ALIASES.keys())

# Known section RSS feeds: domain -> section slug -> feed URL.
SITE_SECTION_FEEDS: dict[str, dict[str, str]] = {
    "bbc.com": {
        "politics": "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "science_and_environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "health": "https://feeds.bbci.co.uk/news/health/rss.xml",
        "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "uk": "https://feeds.bbci.co.uk/news/uk/rss.xml",
        "sport": "https://feeds.bbci.co.uk/news/sport/rss.xml",
        "entertainment": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "entertainment_and_arts": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    },
    "bbc.co.uk": {
        "politics": "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "science_and_environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "health": "https://feeds.bbci.co.uk/news/health/rss.xml",
        "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "uk": "https://feeds.bbci.co.uk/news/uk/rss.xml",
        "sport": "https://feeds.bbci.co.uk/news/sport/rss.xml",
        "entertainment": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "entertainment_and_arts": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    },
    "theguardian.com": {
        "politics": "https://www.theguardian.com/politics/rss",
        "technology": "https://www.theguardian.com/technology/rss",
        "business": "https://www.theguardian.com/business/rss",
        "world": "https://www.theguardian.com/world/rss",
        "uk-news": "https://www.theguardian.com/uk-news/rss",
        "sport": "https://www.theguardian.com/sport/rss",
        "science": "https://www.theguardian.com/science/rss",
        "culture": "https://www.theguardian.com/culture/rss",
    },
    "nytimes.com": {
        "politics": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "world": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "science": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "sports": "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
    },
    "cbc.ca": {
        "politics": "https://www.cbc.ca/cmlink/rss-politics",
        "technology": "https://www.cbc.ca/cmlink/rss-technology",
        "business": "https://www.cbc.ca/cmlink/rss-business",
        "world": "https://www.cbc.ca/cmlink/rss-world",
        "canada": "https://www.cbc.ca/cmlink/rss-canada",
        "health": "https://www.cbc.ca/cmlink/rss-health",
        "sport": "https://www.cbc.ca/cmlink/rss-sports",
        "sports": "https://www.cbc.ca/cmlink/rss-sports",
        "entertainment": "https://www.cbc.ca/cmlink/rss-arts",
        "entertainment_and_arts": "https://www.cbc.ca/cmlink/rss-arts",
    },
}

KNOWN_DOMAIN_FEEDS: dict[str, list[str]] = {
    "bbc.com": ["https://feeds.bbci.co.uk/news/rss.xml"],
    "bbc.co.uk": ["https://feeds.bbci.co.uk/news/rss.xml"],
    "nytimes.com": ["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"],
    "theguardian.com": ["https://www.theguardian.com/world/rss"],
    "reuters.com": ["https://www.reutersagency.com/feed/"],
    "arstechnica.com": ["https://feeds.arstechnica.com/arstechnica/index"],
    "techcrunch.com": ["https://techcrunch.com/feed/"],
    "cbc.ca": ["https://www.cbc.ca/cmlink/rss-topstories"],
    "globalnews.ca": ["https://globalnews.ca/feed/"],
    "thedailystar.net": ["https://www.thedailystar.net/rss.xml"],
}

# RSS URL templates tried when scraping section links from a site's HTML.
SECTION_FEED_TEMPLATES: list[tuple[str, str]] = [
    ("feeds.bbci.co.uk", "https://feeds.bbci.co.uk/news/{section}/rss.xml"),
    ("bbc.co.uk", "https://feeds.bbci.co.uk/news/{section}/rss.xml"),
    ("bbc.com", "https://feeds.bbci.co.uk/news/{section}/rss.xml"),
    ("theguardian.com", "https://www.theguardian.com/{section}/rss"),
    ("nytimes.com", "https://rss.nytimes.com/services/xml/rss/nyt/{Section}.xml"),
]

_NAV_SECTION_RE = re.compile(
    r'href=["\']([^"\']*/(?:news/)?(' + "|".join(re.escape(s) for s in FEED_SECTION_SEGMENTS) + r"))[/\"'?]",
    re.I,
)


def _unique(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def site_domain(site_url: str | None, feed_url: str | None = None) -> str | None:
    for url in (site_url, feed_url):
        if not url:
            continue
        host = urlparse(url).netloc.lower().removeprefix("www.")
        for domain in SITE_SECTION_FEEDS:
            if host == domain or host.endswith(f".{domain}"):
                return domain
    return None


def site_section_map(site_url: str | None, feed_url: str | None = None) -> dict[str, str]:
    domain = site_domain(site_url, feed_url)
    if domain:
        return dict(SITE_SECTION_FEEDS[domain])
    return {}


def topic_name_to_section_slug(topic_name: str, sections: dict[str, str]) -> str | None:
    name = topic_name.strip().lower()
    if name in sections:
        return name
    hyphenated = name.replace(" ", "-")
    if hyphenated in sections:
        return hyphenated
    for section_slug, aliases in SECTION_TOPIC_ALIASES.items():
        if name in aliases and section_slug in sections:
            return section_slug
    return None


def section_feed_for_topic(
    site_url: str | None, feed_url: str | None, topic_name: str
) -> str | None:
    sections = site_section_map(site_url, feed_url)
    if not sections:
        return None
    slug = topic_name_to_section_slug(topic_name, sections)
    return sections.get(slug) if slug else None


def path_section_feed_candidates(url: str) -> list[str]:
    parsed = urlparse(url)
    sections = site_section_map(parsed.netloc, url)
    if not sections:
        return []
    parts = [p for p in parsed.path.lower().split("/") if p]
    out: list[str] = []
    for part in parts:
        if part in sections:
            out.append(sections[part])
    return _unique(out)


def known_feed_candidates(origin: str) -> list[str]:
    host = urlparse(origin).netloc.lower().removeprefix("www.")
    for domain, feeds in KNOWN_DOMAIN_FEEDS.items():
        if host == domain or host.endswith(f".{domain}"):
            return list(feeds)
    return []


def feed_section_from_url(feed_url: str | None) -> str | None:
    if not feed_url:
        return None
    for segment in urlparse(feed_url).path.lower().split("/"):
        if segment in FEED_SECTION_SEGMENTS:
            return segment
    return None


def topic_matches_feed_section(topic_name: str, section: str) -> bool:
    name = topic_name.strip().lower()
    aliases = SECTION_TOPIC_ALIASES.get(section, {section})
    return name in aliases


def resolve_poll_urls(
    feed_url: str, site_url: str | None, topic_names: list[str]
) -> list[str]:
    """URLs to poll for a source given which topics it is routed to."""
    if not topic_names:
        return [feed_url]

    section_urls: list[str] = []
    needs_main = False
    for name in topic_names:
        section_url = section_feed_for_topic(site_url, feed_url, name)
        if section_url:
            section_urls.append(section_url)
        else:
            needs_main = True

    urls = _unique(section_urls)
    if needs_main or not urls:
        urls = _unique(urls + [feed_url])
    return urls


def list_sections_for_site(site_url: str | None, feed_url: str | None) -> list[str]:
    """Human-readable section names available for a site."""
    sections = site_section_map(site_url, feed_url)
    labels: list[str] = []
    seen: set[str] = set()
    for slug in sections:
        label = slug.replace("_", " ").replace("-", " ")
        if label not in seen:
            seen.add(label)
            labels.append(label.title())
    return sorted(labels)


async def _is_valid_feed_url(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.get(url)
        response.raise_for_status()
        parsed = feedparser.parse(response.text)
        if parsed.bozo and not parsed.entries and not parsed.feed.get("title"):
            return False
        return bool(parsed.entries or parsed.feed.get("title"))
    except Exception:
        return False


async def discover_sections_from_html(site_url: str) -> dict[str, str]:
    """Probe a site's HTML navigation for section RSS feeds not in the hardcoded map."""
    domain = site_domain(site_url)
    if domain and domain in SITE_SECTION_FEEDS:
        return dict(SITE_SECTION_FEEDS[domain])

    found: dict[str, str] = {}
    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(site_url)
            response.raise_for_status()
            html = response.text
            base_host = urlparse(str(response.url)).netloc.lower()
            resolved_domain = site_domain(site_url) or ""

            slugs: set[str] = set()
            for match in _NAV_SECTION_RE.finditer(html):
                slugs.add(match.group(2).lower().replace(" ", "-"))

            for slug in slugs:
                for template_host, template in SECTION_FEED_TEMPLATES:
                    if template_host not in base_host and template_host != resolved_domain:
                        continue
                    if template_host == "nytimes.com":
                        candidate = template.format(Section=slug.title())
                    else:
                        candidate = template.format(section=slug)
                    if candidate in found.values():
                        continue
                    if await _is_valid_feed_url(client, candidate):
                        found[slug] = candidate
                        break
    except Exception as exc:
        logger.debug("Section HTML discovery failed for %s: %s", site_url, exc)

    return found


async def enrich_site_sections(site_url: str | None, feed_url: str | None) -> dict[str, str]:
    """Return all known section feeds for a site (hardcoded + scraped)."""
    hardcoded = site_section_map(site_url, feed_url)
    if hardcoded:
        return hardcoded
    if site_url:
        scraped = await discover_sections_from_html(site_url)
        if scraped:
            return scraped
    return {}
