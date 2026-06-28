import re
from html import unescape

# hnrss.org and similar aggregators wrap links in useless HTML.
_HN_BOILERPLATE_RE = re.compile(
    r"article\s+url:|comments\s+url:|news\.ycombinator\.com/item",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Paths that are almost never real news stories.
_JUNK_PATH_RE = re.compile(
    r"/(?:login|signup|register|subscribe|newsletter|account|search|tag|tags|category|topics?|author|authors|about|contact|privacy|terms|cookie|feed|rss|podcast|video|videos|live/[\w-]+)(?:/|$)",
    re.IGNORECASE,
)

_MIN_TITLE_LEN = 12
_MAX_TITLE_LEN = 512


def strip_html_text(text: str | None) -> str:
    if not text:
        return ""
    plain = _TAG_RE.sub(" ", text)
    return unescape(_WS_RE.sub(" ", plain)).strip()


def is_boilerplate_summary(text: str | None) -> bool:
    if not text:
        return False
    return bool(_HN_BOILERPLATE_RE.search(text))


def clean_summary(raw: str | None, *, title: str | None = None) -> str | None:
    if not raw:
        return None
    if is_boilerplate_summary(raw):
        return None
    cleaned = strip_html_text(raw)
    if not cleaned:
        return None
    if title and cleaned.lower() == strip_html_text(title).lower():
        return None
    # Drop summaries that are mostly URLs.
    if cleaned.lower().startswith("http") and " " not in cleaned[:80]:
        return None
    if len(cleaned) < 20 and cleaned.count("http") >= 1:
        return None
    return cleaned[:4000]


def clean_title(raw: str | None, link: str | None = None) -> str | None:
    title = strip_html_text(raw)
    if not title and link:
        title = link
    if not title:
        return None
    if len(title) < _MIN_TITLE_LEN or len(title) > _MAX_TITLE_LEN:
        if link and len(title) >= _MIN_TITLE_LEN:
            pass
        elif len(title) < _MIN_TITLE_LEN:
            return None
        else:
            title = title[:_MAX_TITLE_LEN]
    if title.lower().startswith(("http://", "https://")):
        return None
    # Need a few letters — filters encoding garbage and symbol-only titles.
    letters = sum(1 for c in title if c.isalpha())
    if letters < 8:
        return None
    return title


def is_valid_article_link(link: str | None) -> bool:
    if not link or not link.startswith(("http://", "https://")):
        return False
    if _JUNK_PATH_RE.search(link):
        return False
    # Skip HN discussion threads when the feed is supposed to be news.
    if "news.ycombinator.com/item" in link:
        return False
    return True


def is_valid_parsed_feed(parsed) -> bool:
    """Reject HTML pages and other non-feed responses."""
    if not parsed or not getattr(parsed, "feed", None):
        return False
    version = getattr(parsed, "version", "") or ""
    if version:
        return True
    if parsed.entries:
        return True
    if parsed.feed.get("title") and parsed.feed.get("link"):
        return True
    return False


def should_ingest_entry(entry: dict, link: str | None) -> bool:
    if not is_valid_article_link(link):
        return False
    title = clean_title(entry.get("title"), link)
    if not title:
        return False
    return True
