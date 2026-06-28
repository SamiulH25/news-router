from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1024))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feed: Mapped["Feed"] = relationship(back_populates="articles")
    user_articles: Mapped[list["UserArticle"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )


class UserArticle(Base):
    __tablename__ = "user_articles"
    __table_args__ = (UniqueConstraint("user_id", "article_id", "matched_topic_id", name="uq_user_article_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), index=True)
    matched_topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    surfaced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dwell_ms: Mapped[int] = mapped_column(Integer, default=0)
    opened_full: Mapped[bool] = mapped_column(Boolean, default=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="articles")
    article: Mapped["Article"] = relationship(back_populates="user_articles")
    matched_topic: Mapped["Topic"] = relationship(back_populates="matched_articles")


from app.models.feed import Feed  # noqa: E402
from app.models.topic import Topic  # noqa: E402
from app.models.user import User  # noqa: E402
