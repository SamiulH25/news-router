from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.associations import FeedTopic, UserFeed
from app.models.feed import Feed
from app.models.topic import Topic
from app.models.user import User
from app.schemas.feed import FeedCreate
from app.services.opml import export_opml, parse_opml
from app.routers.feeds import create_feed

router = APIRouter(prefix="/opml", tags=["opml"])


@router.get("/export")
async def export_user_opml(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Feed)
        .join(UserFeed, UserFeed.feed_id == Feed.id)
        .where(UserFeed.user_id == user.id)
        .order_by(Feed.title)
    )
    feeds = [{"title": f.title, "url": f.url, "site_url": f.site_url} for f in result.scalars().all()]
    content = export_opml(feeds)
    return Response(
        content=content,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="news-router.opml"'},
    )


@router.post("/import")
async def import_user_opml(
    file: UploadFile = File(...),
    topic_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw = await file.read()
    try:
        entries = parse_opml(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid OPML: {exc}") from exc

    created = 0
    for entry in entries:
        feed_create = FeedCreate(url=entry["url"], title=entry.get("title"), topic_ids=[topic_id] if topic_id else [])
        if topic_id:
            topic = await db.execute(select(Topic).where(Topic.id == topic_id, Topic.user_id == user.id))
            if not topic.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid topic")
        await create_feed(feed_create, db=db, user=user)
        created += 1
    return {"imported": created}
