from datetime import datetime, timezone
import uuid
from sqlalchemy import ARRAY, JSON, Boolean, Column, DateTime, Enum, Index, Integer, String, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.models.db import engine

class Base(DeclarativeBase):
    pass

class webhook(Base):
    __tablename__ = "webhookevents"
    id =  id = Column(String, primary_key=True, default=uuid.uuid4)
    clerkId = Column(String , unique=True)
    type: Mapped[dict] = Column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


    


