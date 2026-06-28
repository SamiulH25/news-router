from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    keywords: str = ""
    exclude_keywords: str = ""
    feed_ids: list[int] = Field(default_factory=list)


class TopicUpdate(BaseModel):
    name: str | None = None
    keywords: str | None = None
    exclude_keywords: str | None = None
    feed_ids: list[int] | None = None


class TopicResponse(BaseModel):
    id: int
    name: str
    keywords: str
    exclude_keywords: str = ""
    feed_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}
