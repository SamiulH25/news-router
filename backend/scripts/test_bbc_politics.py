import asyncio

from app.services.feed_discovery import discover_feed_from_site
from app.services.section_feeds import resolve_poll_urls, section_feed_for_topic


async def main() -> None:
    discovered = await discover_feed_from_site("bbc.com")
    print("bbc.com main feed:", discovered["feed_url"])
    print("sections:", discovered.get("sections"))

    politics_url = section_feed_for_topic(
        discovered.get("site_url"), discovered["feed_url"], "Politics"
    )
    print("Politics section feed:", politics_url)

    poll_urls = resolve_poll_urls(
        discovered["feed_url"], discovered.get("site_url"), ["Politics"]
    )
    print("Poll URLs when Politics linked:", poll_urls)

    poll_urls_mixed = resolve_poll_urls(
        discovered["feed_url"], discovered.get("site_url"), ["Politics", "General"]
    )
    print("Poll URLs when Politics + General:", poll_urls_mixed)


if __name__ == "__main__":
    asyncio.run(main())
