from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserAffinity(Base):
    """Learned taste profile — topic, source, and keyword weights per user."""

    __tablename__ = "user_affinities"
    __table_args__ = (UniqueConstraint("user_id", "kind", "key", name="uq_user_affinity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)  # topic | feed | keyword
    key: Mapped[str] = mapped_column(String(128), index=True)
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="affinities")


from app.models.user import User  # noqa: E402
