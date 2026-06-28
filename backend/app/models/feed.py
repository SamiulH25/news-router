from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    favicon_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    site_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_fetch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list["Article"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
    topics: Mapped[list["FeedTopic"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
    subscribers: Mapped[list["UserFeed"]] = relationship(back_populates="feed", cascade="all, delete-orphan")


from app.models.article import Article  # noqa: E402
from app.models.associations import FeedTopic, UserFeed  # noqa: E402
