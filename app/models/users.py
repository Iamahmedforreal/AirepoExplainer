
import enum
import uuid
from enum import Enum as PyEnum
from sqlalchemy import ARRAY, Boolean, Column, DateTime, Enum, Index, Integer, String, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship
from app.models.db import engine

class Base(DeclarativeBase):
    pass

class RepoStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    userId = Column(String, ForeignKey("users.id"), nullable=False)

    githubUrl = Column(String, nullable=False)
    repoName = Column(String, nullable=True)
    repoOwner = Column(String, nullable=True)
    defaultBranch = Column(String, nullable=True)

    isPrivate = Column(Boolean, default=False, nullable=False)
    sizeKb = Column(Integer, nullable=True)

    description = Column(String, nullable=True)
    language = Column(String, nullable=True)

    topics = Column(ARRAY(String), nullable=True)

    stars = Column(Integer, nullable=True)
    license = Column(String, nullable=True)

    isArchived = Column(Boolean, default=False, nullable=False)

    repoCreatedAt = Column(DateTime(timezone=True), nullable=True)
    repoUpdatedAt = Column(DateTime(timezone=True), nullable=True)

    status = Column(Enum(RepoStatus , name="repo_status_enum"), default=RepoStatus.PENDING, nullable=False)

    # Relationship
    user = relationship("User", back_populates="repositories")

  
   #ingestionJobs = relationship("IngestionJob", back_populates="repository")

    
    __table_args__ = (
        UniqueConstraint("userId", "githubUrl", name="uq_user_repo_url"),
        Index("ix_repositories_userId", "userId"),
        Index("ix_repositories_language", "language"),
        Index("ix_repositories_status", "status"),
    )

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


