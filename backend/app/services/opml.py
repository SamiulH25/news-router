import xml.etree.ElementTree as ET
from html import escape


def export_opml(feeds: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        "  <head><title>News Router Feeds</title></head>",
        "  <body>",
    ]
    for feed in feeds:
        title = escape(feed["title"], quote=True)
        url = escape(feed["url"], quote=True)
        html_url = escape(feed.get("site_url") or feed["url"], quote=True)
        lines.append(f'    <outline type="rss" text="{title}" title="{title}" xmlUrl="{url}" htmlUrl="{html_url}" />')
    lines.extend(["  </body>", "</opml>"])
    return "\n".join(lines)


def parse_opml(content: str) -> list[dict]:
    root = ET.fromstring(content)
    feeds: list[dict] = []
    for outline in root.iter("outline"):
        xml_url = outline.attrib.get("xmlUrl") or outline.attrib.get("xmlurl")
        if not xml_url:
            continue
        feeds.append(
            {
                "url": xml_url,
                "title": outline.attrib.get("title") or outline.attrib.get("text") or xml_url,
                "site_url": outline.attrib.get("htmlUrl") or outline.attrib.get("htmlurl"),
            }
        )
    return feeds
