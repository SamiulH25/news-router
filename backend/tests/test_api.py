import pytest
from httpx import AsyncClient

from app.data.default_feeds import DEFAULT_NEWS_OUTLETS


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["poll_api_version"] == 2


@pytest.mark.asyncio
async def test_auth_config(client: AsyncClient):
    response = await client.get("/api/auth/config")
    assert response.status_code == 200
    assert "allow_registration" in response.json()


@pytest.mark.asyncio
async def test_register_login_and_me(client: AsyncClient):
    register = await client.post(
        "/api/auth/register",
        json={"username": "household", "password": "secret123"},
    )
    assert register.status_code == 200
    user = register.json()
    assert user["username"] == "household"
    assert user["is_admin"] is True

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "household"

    await client.post("/api/auth/logout")
    denied = await client.get("/api/auth/me")
    assert denied.status_code == 401

    login = await client.post(
        "/api/auth/login",
        json={"username": "household", "password": "secret123"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_daily_feed_requires_auth(client: AsyncClient):
    response = await client.get("/api/articles/feed")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_onboarding_catalog(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "catalog", "password": "secret123"},
    )
    response = await client.get("/api/onboarding/catalog")
    assert response.status_code == 200
    data = response.json()
    assert len(data["countries"]) >= 10
    assert len(data["default_selected_urls"]) >= 3
    canada = next(c for c in data["countries"] if c["code"] == "CA")
    assert len(canada["outlets"]) >= 2
    assert any(o["title"] == "CBC News" for o in canada["outlets"])


@pytest.mark.asyncio
async def test_onboarding_defaults(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "newbie", "password": "secret123"},
    )
    response = await client.get("/api/onboarding/defaults")
    assert response.status_code == 200
    outlets = response.json()
    assert len(outlets) == len(DEFAULT_NEWS_OUTLETS)
    canada = [item for item in outlets if item["region"] == "Canada"]
    assert len(canada) >= 2


@pytest.mark.asyncio
async def test_onboarding_complete_seeds_feeds(client: AsyncClient, monkeypatch):
    await client.post(
        "/api/auth/register",
        json={"username": "setup", "password": "secret123"},
    )

    async def fake_subscribe(db, user, *, url, title=None, topic_ids=None, poll=True, route=True):
        from app.models.associations import UserFeed
        from app.models.feed import Feed

        feed = Feed(url=url, title=title or url, site_url=None, favicon_url=None)
        db.add(feed)
        await db.flush()
        db.add(UserFeed(user_id=user.id, feed_id=feed.id))
        await db.flush()
        return feed

    monkeypatch.setattr("app.services.default_feeds.subscribe_user_to_feed", fake_subscribe)

    complete = await client.post(
        "/api/onboarding/complete",
        json={
            "timezone": "America/Toronto",
            "topic_name": "Headlines",
            "selected_outlet_urls": [
                "https://www.cbc.ca/webfeed/rss/rss-topstories",
                "https://globalnews.ca/feed/",
                "https://www.thedailystar.net/rss.xml",
            ],
        },
    )
    assert complete.status_code == 200
    assert complete.json()["onboarded"] is True

    feeds = await client.get("/api/feeds")
    assert feeds.status_code == 200
    assert len(feeds.json()) == 3
    titles = {feed["title"] for feed in feeds.json()}
    assert titles == {"CBC News", "Global News", "The Daily Star"}


@pytest.mark.asyncio
async def test_onboarding_complete_requires_source(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "empty", "password": "secret123"},
    )
    complete = await client.post(
        "/api/onboarding/complete",
        json={"timezone": "UTC", "topic_name": "Headlines", "selected_outlet_urls": []},
    )
    assert complete.status_code == 400


@pytest.mark.asyncio
async def test_empty_daily_feed(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "reader", "password": "secret123"},
    )
    response = await client.get("/api/articles/feed")
    assert response.status_code == 200
    body = response.json()
    assert body["groups"] == []
    assert body["total_unread"] == 0
