from datetime import datetime, timezone
import uuid
from sqlalchemy import ARRAY, JSON, Boolean, Column, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.users import Base
from app.models.db import engine

class webhook(Base):
    __tablename__ = "webhookevents"
    id =  id = Column(String, primary_key=True, default=uuid.uuid4)
    clerkId = Column(String , unique=True)
    type: Mapped[dict] = Column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    

    
