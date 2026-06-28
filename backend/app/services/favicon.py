from urllib.parse import urljoin, urlparse

import httpx

USER_AGENT = "NewsRouter/1.0"


async def fetch_favicon_url(site_url: str) -> str | None:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    origin = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        urljoin(origin, "/favicon.ico"),
        f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64",
    ]
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for candidate in candidates:
            try:
                if "google.com" in candidate:
                    return candidate
                response = await client.head(candidate)
                if response.status_code < 400:
                    return candidate
            except httpx.HTTPError:
                continue
    return f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64"
