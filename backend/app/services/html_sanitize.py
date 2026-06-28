import re

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "blockquote",
    "figure",
    "figcaption",
    "img",
]
ALLOWED_ATTRS = {"a": ["href", "title", "rel"], "img": ["src", "alt", "title"]}


def sanitize_html(html: str | None) -> str | None:
    if not html:
        return None
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return cleaned or None
