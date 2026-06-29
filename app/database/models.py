from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RunHistory(Base):
    __tablename__ = "run_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    status = Column(String, default="pending")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class Approval(Base):
    __tablename__ = "approval"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, nullable=False, index=True)
    reviewer = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
