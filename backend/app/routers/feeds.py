import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.associations import FeedTopic, UserFeed
from app.models.feed import Feed
from app.models.user import User
from app.schemas.feed import FeedCreate, FeedPreviewRequest, FeedPreviewResponse, FeedResponse, FeedUpdate
from app.services.feed_discovery import discover_feed_from_site
from app.services.feed_fetcher import poll_single_feed, route_existing_feed_articles
from app.services.feed_subscribe import set_feed_topics, subscribe_user_to_feed

router = APIRouter(prefix="/feeds", tags=["feeds"])
logger = logging.getLogger(__name__)


async def _feed_response(db: AsyncSession, feed: Feed, user_id: int) -> FeedResponse:
    topic_result = await db.execute(
        select(FeedTopic.topic_id).where(FeedTopic.feed_id == feed.id, FeedTopic.user_id == user_id)
    )
    topic_ids = list(topic_result.scalars().all())
    sub = await db.execute(select(UserFeed).where(UserFeed.user_id == user_id, UserFeed.feed_id == feed.id))
    return FeedResponse(
        id=feed.id,
        url=feed.url,
        title=feed.title,
        favicon_url=feed.favicon_url,
        site_url=feed.site_url,
        last_fetched_at=feed.last_fetched_at,
        last_successful_fetch=feed.last_successful_fetch,
        last_error=feed.last_error,
        topic_ids=topic_ids,
        is_subscribed=sub.scalar_one_or_none() is not None,
    )


@router.get("", response_model=list[FeedResponse])
async def list_feeds(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Feed)
        .join(UserFeed, UserFeed.feed_id == Feed.id)
        .where(UserFeed.user_id == user.id)
        .order_by(Feed.title)
    )
    feeds = result.scalars().all()
    return [await _feed_response(db, feed, user.id) for feed in feeds]


@router.post("/preview", response_model=FeedPreviewResponse)
async def preview_feed(body: FeedPreviewRequest, user: User = Depends(get_current_user)):
    try:
        discovered = await discover_feed_from_site(body.url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not find a feed for that site: {exc}"
        ) from exc
    return FeedPreviewResponse(
        feed_url=discovered["feed_url"],
        title=discovered["title"],
        site_url=discovered.get("site_url"),
        input_url=body.url.strip(),
        sections=discovered.get("sections", []),
    )


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
async def create_feed(body: FeedCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        feed = await subscribe_user_to_feed(
            db,
            user,
            url=body.url,
            title=body.title,
            topic_ids=list(body.topic_ids) or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not add that site: {exc}"
        ) from exc

    await db.commit()
    await db.refresh(feed)
    return await _feed_response(db, feed, user.id)


@router.patch("/{feed_id}", response_model=FeedResponse)
async def update_feed(
    feed_id: int,
    body: FeedUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    feed = await _get_user_feed(db, user.id, feed_id)
    if body.title is not None:
        feed.title = body.title
    if body.topic_ids is not None:
        await set_feed_topics(db, user, feed.id, body.topic_ids)
        await route_existing_feed_articles(db, feed)
    await db.commit()
    await db.refresh(feed)
    return await _feed_response(db, feed, user.id)


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_feed(feed_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UserFeed).where(UserFeed.user_id == user.id, UserFeed.feed_id == feed_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    await db.delete(row)
    await db.commit()


@router.post("/{feed_id}/poll")
async def poll_feed(feed_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    feed = await _get_user_feed(db, user.id, feed_id)
    detail = await poll_single_feed(db, feed)
    await route_existing_feed_articles(db, feed)
    await db.commit()
    return detail


async def _get_user_feed(db: AsyncSession, user_id: int, feed_id: int) -> Feed:
    result = await db.execute(
        select(Feed)
        .join(UserFeed, UserFeed.feed_id == Feed.id)
        .where(UserFeed.user_id == user_id, Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    return feed
