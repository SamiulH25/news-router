from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class FeedCreate(BaseModel):
    url: str = Field(max_length=2048)
    title: str | None = None
    topic_ids: list[int] = Field(default_factory=list)


class FeedUpdate(BaseModel):
    title: str | None = None
    topic_ids: list[int] | None = None


class FeedResponse(BaseModel):
    id: int
    url: str
    title: str
    favicon_url: str | None
    site_url: str | None
    last_fetched_at: datetime | None
    last_successful_fetch: datetime | None
    last_error: str | None
    topic_ids: list[int] = Field(default_factory=list)
    is_subscribed: bool = True

    model_config = {"from_attributes": True}


class FeedPreviewRequest(BaseModel):
    url: str = Field(description="Website URL or RSS feed URL")


class FeedPreviewResponse(BaseModel):
    feed_url: str
    title: str
    site_url: str | None
    input_url: str
    sections: list[str] = Field(default_factory=list)
