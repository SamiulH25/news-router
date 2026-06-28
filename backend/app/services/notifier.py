import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_ntfy_notification(topic: str, title: str, message: str, click_url: str | None = None) -> bool:
    if not topic:
        return False
    base = settings.ntfy_base_url.rstrip("/")
    url = f"{base}/{topic}"
    headers = {"Title": title, "Priority": "default", "Tags": "newspaper"}
    if click_url:
        headers["Click"] = click_url
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, content=message, headers=headers)
            response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("ntfy notification failed for topic %s: %s", topic, exc)
        return False
