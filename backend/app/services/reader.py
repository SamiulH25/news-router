import logging

import httpx
import trafilatura
from trafilatura.metadata import extract_metadata

from app.services.entry_images import image_from_html, upscale_image_url
from app.services.rss_http import USER_AGENT

logger = logging.getLogger(__name__)


async def extract_article_content(url: str) -> tuple[str | None, str | None]:
    """Return (content_html, image_url)."""
    try:
        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
        downloaded = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="html")
        image_url = None
        try:
            metadata = extract_metadata(html, default_url=url)
            if metadata and metadata.image:
                image_url = upscale_image_url(metadata.image)
        except Exception:
            pass
        if not image_url:
            image_url = image_from_html(downloaded or html, url)
        return downloaded, image_url
    except Exception as exc:
        logger.warning("Failed to extract article %s: %s", url, exc)
        return None, None
