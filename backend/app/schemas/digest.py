from pydantic import BaseModel, Field


class PollUrlResult(BaseModel):
    url: str
    entries_in_feed: int = 0
    new_articles: int = 0
    routed_to_topics: int = 0
    error: str | None = None


class PollFeedResult(BaseModel):
    feed_id: int
    feed_title: str
    topics: list[str] = Field(default_factory=list)
    poll_urls: list[str] = Field(default_factory=list)
    new_articles: int = 0
    routed_to_topics: int = 0
    url_results: list[PollUrlResult] = Field(default_factory=list)
    error: str | None = None


class PollResponse(BaseModel):
    new_articles: int = 0
    feeds: list[PollFeedResult] = Field(default_factory=list)
    edition_stories: int | None = None
