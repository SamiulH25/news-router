from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    keywords: Mapped[str] = mapped_column(Text, default="")
    exclude_keywords: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="owned_topics")
    feeds: Mapped[list["FeedTopic"]] = relationship(back_populates="topic", cascade="all, delete-orphan")
    matched_articles: Mapped[list["UserArticle"]] = relationship(back_populates="matched_topic")


from app.models.article import UserArticle  # noqa: E402
from app.models.associations import FeedTopic  # noqa: E402
from app.models.user import User  # noqa: E402
