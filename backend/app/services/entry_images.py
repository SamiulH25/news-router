import re
from urllib.parse import urljoin, urlparse

_IMG_SRC_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)
_BBC_ICHEF_RE = re.compile(r"(ichef\.bbci\.co\.uk/ace/standard/)\d+(/cps)")

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")


def _is_image_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _IMAGE_EXTENSIONS) or "/image/" in path


def _normalize_image_url(url: str, base_url: str | None = None) -> str | None:
    if not url or url.startswith("data:"):
        return None
    url = url.strip()
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)
    if not url.startswith(("http://", "https://")):
        return None
    return upscale_image_url(url)


def upscale_image_url(url: str) -> str:
    """Use a larger BBC thumbnail when the feed only ships a small one."""
    return _BBC_ICHEF_RE.sub(r"\g<1>976\g<2>", url)


def image_from_html(html: str | None, base_url: str | None = None) -> str | None:
    if not html:
        return None
    match = _IMG_SRC_RE.search(html)
    if not match:
        return None
    return _normalize_image_url(match.group(1), base_url)


def entry_image_url(entry: dict, base_url: str | None = None) -> str | None:
    """Best-effort hero image from an RSS/Atom entry."""
    thumbs = entry.get("media_thumbnail")
    if thumbs:
        items = thumbs if isinstance(thumbs, list) else [thumbs]
        for item in items:
            url = item.get("url") if isinstance(item, dict) else None
            normalized = _normalize_image_url(url, base_url) if url else None
            if normalized:
                return normalized

    for item in entry.get("media_content") or []:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        medium = (item.get("medium") or "").lower()
        mime = (item.get("type") or "").lower()
        if url and (medium == "image" or mime.startswith("image/")):
            normalized = _normalize_image_url(url, base_url)
            if normalized:
                return normalized

    for enc in entry.get("enclosures") or []:
        if not isinstance(enc, dict):
            continue
        mime = (enc.get("type") or "").lower()
        href = enc.get("href") or enc.get("url")
        if href and mime.startswith("image/"):
            normalized = _normalize_image_url(href, base_url)
            if normalized:
                return normalized

    for link in entry.get("links") or []:
        if not isinstance(link, dict):
            continue
        mime = (link.get("type") or "").lower()
        href = link.get("href")
        if href and mime.startswith("image/"):
            normalized = _normalize_image_url(href, base_url)
            if normalized:
                return normalized
        rel = (link.get("rel") or "").lower()
        if href and rel == "enclosure" and _is_image_url(href):
            normalized = _normalize_image_url(href, base_url)
            if normalized:
                return normalized

    for key in ("summary", "description", "content"):
        raw = entry.get(key)
        if isinstance(raw, list) and raw:
            raw = raw[0].get("value") if isinstance(raw[0], dict) else raw[0]
        if isinstance(raw, str):
            found = image_from_html(raw, base_url)
            if found:
                return found

    return None
