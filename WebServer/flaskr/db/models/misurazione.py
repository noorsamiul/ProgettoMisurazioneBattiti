# db/models/misurazione.py
from typing import TYPE_CHECKING
from ..base import Base
from sqlalchemy import Integer, DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone


if TYPE_CHECKING:
    from .user import User  

class Misurazione(Base):
    __tablename__ = "Misurazione"

    bpmMedi: Mapped[int] = mapped_column(Integer, nullable=False)
    bpmMax:  Mapped[int] = mapped_column(Integer, nullable=False)
    bpmMin:  Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("User.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="misurazioni")

    @classmethod
    def get_by_user(cls, session, user_id: str, ordina: bool = True):
        from sqlalchemy import desc
        query = select(cls).where(cls.user_id == user_id)
        if ordina:
            query = query.order_by(desc(cls.data))
        return session.execute(query).scalars().all()