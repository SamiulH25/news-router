from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserFeed(Base):
    __tablename__ = "user_feeds"
    __table_args__ = (UniqueConstraint("user_id", "feed_id", name="uq_user_feed"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"), index=True)

    user: Mapped["User"] = relationship(back_populates="feeds")
    feed: Mapped["Feed"] = relationship(back_populates="subscribers")


class FeedTopic(Base):
    """Per-user routing: which topics receive stories from a shared source."""

    __tablename__ = "feed_topics"
    __table_args__ = (UniqueConstraint("user_id", "feed_id", "topic_id", name="uq_user_feed_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)

    user: Mapped["User"] = relationship(back_populates="feed_topics")
    feed: Mapped["Feed"] = relationship(back_populates="topics")
    topic: Mapped["Topic"] = relationship(back_populates="feeds")


from app.models.feed import Feed  # noqa: E402
from app.models.topic import Topic  # noqa: E402
from app.models.user import User  # noqa: E402
