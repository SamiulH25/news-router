from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    ntfy_topic: Mapped[str | None] = mapped_column(String(128), nullable=True)
    digest_hour: Mapped[int] = mapped_column(Integer, default=7)
    digest_minute: Mapped[int] = mapped_column(Integer, default=0)
    digest_evening_hour: Mapped[int] = mapped_column(Integer, default=19)
    digest_evening_minute: Mapped[int] = mapped_column(Integer, default=0)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    feed_window_hours: Mapped[int] = mapped_column(Integer, default=12)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    last_edition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    personalized_feed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feeds: Mapped[list["UserFeed"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    feed_topics: Mapped[list["FeedTopic"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    owned_topics: Mapped[list["Topic"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    articles: Mapped[list["UserArticle"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    affinities: Mapped[list["UserAffinity"]] = relationship(back_populates="user", cascade="all, delete-orphan")


from app.models.article import UserArticle  # noqa: E402
from app.models.associations import FeedTopic, UserFeed  # noqa: E402
from app.models.topic import Topic  # noqa: E402
