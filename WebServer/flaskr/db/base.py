# db/base.py
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, inspect
from .engine import SessionLocal


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    @classmethod
    def session(cls):
        return SessionLocal()

    @property
    def persistent(self):
        return inspect(self).persistent