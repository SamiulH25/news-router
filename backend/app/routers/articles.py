from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.article import Article, UserArticle
from app.models.user import User
from app.schemas.article import (
    ArticleReadResponse,
    ArticleSummary,
    DailyFeedResponse,
    EngagementRequest,
    TopicFeedGroup,
)
from app.services.entry_images import image_from_html
from app.services.entry_quality import clean_summary
from app.services.feed_ranker import rank_timeline, rank_within_groups
from app.services.feed_window import user_article_in_window
from app.services.html_sanitize import sanitize_html
from app.services.preference_learning import load_affinity_map, record_engagement
from app.services.reader import extract_article_content
from app.services.story_cluster import cluster_key

router = APIRouter(prefix="/articles", tags=["articles"])


def _article_image_url(article: Article) -> str | None:
    if article.image_url:
        return article.image_url
    return image_from_html(article.summary, article.url)


def _to_summary(row: UserArticle, *, rank_score: float | None = None) -> ArticleSummary:
    article = row.article
    return ArticleSummary(
        id=article.id,
        user_article_id=row.id,
        title=article.title,
        url=article.url,
        summary=clean_summary(article.summary, title=article.title),
        image_url=_article_image_url(article),
        published_at=article.published_at,
        is_read=row.is_read,
        feed_title=article.feed.title,
        feed_id=article.feed_id,
        favicon_url=article.feed.favicon_url,
        surfaced_at=row.surfaced_at,
        archived_at=row.archived_at,
        cluster_key=cluster_key(article.title),
        rank_score=rank_score,
    )


def _group_user_articles(
    rows: list[UserArticle],
    *,
    edition_fetched_at=None,
    personalized: bool = False,
    timeline: list[ArticleSummary] | None = None,
) -> DailyFeedResponse:
    groups: dict[int, TopicFeedGroup] = {}
    total_unread = 0
    for row in rows:
        topic = row.matched_topic
        if topic.id not in groups:
            groups[topic.id] = TopicFeedGroup(
                topic_id=topic.id,
                topic_name=topic.name,
                articles=[],
                unread_count=0,
            )
        if not row.is_read:
            groups[topic.id].unread_count += 1
            total_unread += 1
        summary = next((t for t in (timeline or []) if t.user_article_id == row.id), None)
        groups[topic.id].articles.append(summary or _to_summary(row))

    ordered_groups = sorted(groups.values(), key=lambda g: g.topic_name.lower())
    return DailyFeedResponse(
        groups=ordered_groups,
        total_unread=total_unread,
        edition_fetched_at=edition_fetched_at,
        personalized=personalized,
        timeline=timeline or [],
    )


async def _apply_personalized_order(
    db: AsyncSession,
    user: User,
    rows: list[UserArticle],
    *,
    window_hours: int,
    interleaved: bool,
) -> tuple[list[UserArticle], list[ArticleSummary]]:
    profile = await load_affinity_map(db, user.id)
    if interleaved:
        ranked = rank_timeline(rows, profile, window_hours=window_hours)
    else:
        ranked = rank_within_groups(rows, profile, window_hours=window_hours)

    from app.services.preference_learning import affinity_score

    timeline = [
        _to_summary(
            row,
            rank_score=round(
                affinity_score(
                    profile,
                    topic_id=row.matched_topic_id,
                    feed_id=row.article.feed_id,
                    title=row.article.title,
                ),
                4,
            ),
        )
        for row in ranked
    ]
    return ranked, timeline


@router.get("/feed", response_model=DailyFeedResponse)
async def get_daily_feed(
    hours: int | None = None,
    topic_id: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    window_hours = hours if hours is not None else user.feed_window_hours
    query = (
        select(UserArticle)
        .join(Article)
        .where(
            UserArticle.user_id == user.id,
            UserArticle.archived_at.is_(None),
            user_article_in_window(window_hours),
        )
        .options(
            selectinload(UserArticle.article).selectinload(Article.feed),
            selectinload(UserArticle.matched_topic),
        )
    )
    if topic_id is not None:
        query = query.where(UserArticle.matched_topic_id == topic_id)
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                Article.title.ilike(needle),
                Article.summary.ilike(needle),
            )
        )
    else:
        query = query.order_by(UserArticle.surfaced_at.desc())

    result = await db.execute(query)
    rows = list(result.scalars().all())

    personalized = bool(user.personalized_feed and not q)
    timeline: list[ArticleSummary] | None = None
    if personalized and rows:
        rows, timeline = await _apply_personalized_order(
            db, user, rows, window_hours=window_hours, interleaved=topic_id is None
        )

    return _group_user_articles(
        rows,
        edition_fetched_at=user.last_edition_at,
        personalized=personalized,
        timeline=timeline,
    )


@router.get("/search", response_model=DailyFeedResponse)
async def search_articles(
    q: str = Query(min_length=1, max_length=200),
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    needle = f"%{q.strip().lower()}%"
    query = (
        select(UserArticle)
        .join(Article)
        .where(
            UserArticle.user_id == user.id,
            or_(Article.title.ilike(needle), Article.summary.ilike(needle)),
        )
        .options(
            selectinload(UserArticle.article).selectinload(Article.feed),
            selectinload(UserArticle.matched_topic),
        )
        .order_by(UserArticle.surfaced_at.desc())
        .limit(100)
    )
    if not include_archived:
        query = query.where(UserArticle.archived_at.is_(None))
    result = await db.execute(query)
    return _group_user_articles(list(result.scalars().all()))


@router.get("/archive", response_model=DailyFeedResponse)
async def get_archived_feed(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.feed_edition import load_archived_feed

    rows = await load_archived_feed(db, user)
    return _group_user_articles(rows)


@router.post("/user-articles/{user_article_id}/engage")
async def engage_article(
    user_article_id: int,
    body: EngagementRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArticle)
        .where(UserArticle.id == user_article_id, UserArticle.user_id == user.id)
        .options(selectinload(UserArticle.article))
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if body.event not in {"open", "less"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event")
    await record_engagement(db, row, event=body.event)
    if body.event == "open":
        row.is_read = True
    await db.commit()
    return {"ok": True}


@router.get("/{article_id}/read", response_model=ArticleReadResponse)
async def read_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArticle)
        .where(UserArticle.user_id == user.id, UserArticle.article_id == article_id)
        .options(selectinload(UserArticle.article).selectinload(Article.feed))
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    article = row.article
    content_html, extracted_image = await extract_article_content(article.url)
    content_html = sanitize_html(content_html)
    if extracted_image and not article.image_url:
        article.image_url = extracted_image
    row.is_read = True
    row.opened_full = True
    await db.commit()
    return ArticleReadResponse(
        id=article.id,
        user_article_id=row.id,
        title=article.title,
        url=article.url,
        content_html=content_html,
        image_url=_article_image_url(article),
        feed_title=article.feed.title,
    )


@router.post("/user-articles/{user_article_id}/read")
async def mark_read(
    user_article_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArticle).where(UserArticle.id == user_article_id, UserArticle.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    row.is_read = True
    await db.commit()
    return {"ok": True}


@router.post("/user-articles/{user_article_id}/unread")
async def mark_unread(
    user_article_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserArticle).where(UserArticle.id == user_article_id, UserArticle.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    row.is_read = False
    await db.commit()
    return {"ok": True}
