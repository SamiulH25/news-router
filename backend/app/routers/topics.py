from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.associations import FeedTopic, UserFeed
from app.models.feed import Feed
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
from app.services.feed_fetcher import route_existing_feed_articles

router = APIRouter(prefix="/topics", tags=["topics"])


async def _topic_response(db: AsyncSession, topic: Topic, user_id: int) -> TopicResponse:
    result = await db.execute(
        select(FeedTopic.feed_id).where(FeedTopic.topic_id == topic.id, FeedTopic.user_id == user_id)
    )
    return TopicResponse(
        id=topic.id,
        name=topic.name,
        keywords=topic.keywords,
        exclude_keywords=topic.exclude_keywords or "",
        feed_ids=list(result.scalars().all()),
    )


@router.get("", response_model=list[TopicResponse])
async def list_topics(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Topic).where(Topic.user_id == user.id).order_by(Topic.name))
    topics = result.scalars().all()
    return [await _topic_response(db, topic, user.id) for topic in topics]


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(body: TopicCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    topic = Topic(
        user_id=user.id,
        name=body.name,
        keywords=body.keywords,
        exclude_keywords=body.exclude_keywords,
    )
    db.add(topic)
    await db.flush()
    if body.feed_ids:
        await _set_topic_feeds(db, user, topic.id, body.feed_ids)
        await _route_feeds_for_topic(db, body.feed_ids)
    await db.commit()
    await db.refresh(topic)
    return await _topic_response(db, topic, user.id)


@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    body: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    topic = await _get_user_topic(db, user.id, topic_id)
    if body.name is not None:
        topic.name = body.name
    if body.keywords is not None:
        topic.keywords = body.keywords
    if body.exclude_keywords is not None:
        topic.exclude_keywords = body.exclude_keywords
    if body.feed_ids is not None:
        await _set_topic_feeds(db, user, topic.id, body.feed_ids)
        await _route_feeds_for_topic(db, body.feed_ids)
    await db.commit()
    await db.refresh(topic)
    return await _topic_response(db, topic, user.id)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    topic = await _get_user_topic(db, user.id, topic_id)
    await db.delete(topic)
    await db.commit()


async def _get_user_topic(db: AsyncSession, user_id: int, topic_id: int) -> Topic:
    result = await db.execute(select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


async def _route_feeds_for_topic(db: AsyncSession, feed_ids: list[int]) -> None:
    if not feed_ids:
        return
    result = await db.execute(select(Feed).where(Feed.id.in_(feed_ids)))
    for feed in result.scalars().all():
        await route_existing_feed_articles(db, feed)


async def _set_topic_feeds(db: AsyncSession, user: User, topic_id: int, feed_ids: list[int]) -> None:
    subbed = await db.execute(
        select(UserFeed.feed_id).where(UserFeed.user_id == user.id, UserFeed.feed_id.in_(feed_ids))
    )
    allowed = set(subbed.scalars().all())
    if len(allowed) != len(set(feed_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feed selection")
    existing = await db.execute(
        select(FeedTopic).where(FeedTopic.topic_id == topic_id, FeedTopic.user_id == user.id)
    )
    current = {link.feed_id: link for link in existing.scalars().all()}
    for feed_id in feed_ids:
        if feed_id not in current:
            db.add(FeedTopic(user_id=user.id, feed_id=feed_id, topic_id=topic_id))
    for feed_id, link in current.items():
        if feed_id not in set(feed_ids):
            await db.delete(link)
