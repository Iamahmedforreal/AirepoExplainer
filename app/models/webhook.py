from datetime import datetime, timezone
import uuid
from sqlalchemy import  JSON,  DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.users import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"   

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_id: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
