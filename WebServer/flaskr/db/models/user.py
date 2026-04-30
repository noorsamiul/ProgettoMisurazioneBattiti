# db/models/user.py
from ..base import Base, SessionLocal
from sqlalchemy import String, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "User"

    username: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    misurazioni: Mapped[list["Misurazione"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @classmethod
    def get_user(cls, session, username: str):
        query = select(cls).where(cls.username == username)
        return session.execute(query).scalars().first()

    def login(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def set_password(self, password: str):
        self.password = generate_password_hash(password)