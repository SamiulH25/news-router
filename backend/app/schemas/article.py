from datetime import datetime

from pydantic import BaseModel, Field


class ArticleSummary(BaseModel):
    id: int
    user_article_id: int
    title: str
    url: str
    summary: str | None
    image_url: str | None
    published_at: datetime | None
    is_read: bool
    feed_title: str
    feed_id: int
    favicon_url: str | None
    surfaced_at: datetime | None = None
    archived_at: datetime | None = None
    cluster_key: str | None = None
    rank_score: float | None = None


class TopicFeedGroup(BaseModel):
    topic_id: int
    topic_name: str
    articles: list[ArticleSummary]
    unread_count: int


class DailyFeedResponse(BaseModel):
    groups: list[TopicFeedGroup]
    total_unread: int
    edition_fetched_at: datetime | None = None
    personalized: bool = False
    timeline: list[ArticleSummary] = Field(default_factory=list)


class EngagementRequest(BaseModel):
    event: str  # open | less


class ArticleReadResponse(BaseModel):
    id: int
    user_article_id: int | None = None
    title: str
    url: str
    content_html: str | None
    image_url: str | None
    feed_title: str
