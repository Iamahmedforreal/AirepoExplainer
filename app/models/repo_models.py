"""
Database schema for the codebase intelligence platform.

Tables:
    users           - platform accounts, created via Clerk webhook
    repositories    - GitHub repos submitted for indexing
    worker_tasks    - background job tracking per repo
    webhook_events  - raw GitHub webhook ingestion log
    conversations   - chat sessions between a user and a repo
    messages        - individual turns within a conversation
"""
import enum
import uuid
from sqlalchemy import (
    ARRAY, JSON, Boolean, Column, DateTime,
    Enum, Index, Integer, String, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship
from app.models.db import engine


class Base(DeclarativeBase):
    pass



# Enumerations

class RepoStatus(enum.Enum):
    PENDING  = "pending"
    INDEXING = "indexing"
    INDEXED  = "indexed"
    FAILED   = "failed"
    OUTDATED = "outdated"


class TaskType(enum.Enum):
    """
    Granularity of a worker job.
    FULL_PIPELINE runs all stages in a single ARQ task.
    Individual types are reserved for partial re-runs (e.g. re-embed only).
    """
    FULL_PIPELINE = "full_pipeline"
    CLONE="clone"
    CHUNK="chunk"
    EMBED="embed"


class TaskStatus(enum.Enum):
    """
    Execution state of a single WorkerTask row.
    RETRYING means attempts > 1 but < maxAttempts and job is back in the queue.
    """
    PENDING  = "pending"
    RUNNING  = "running"
    RETRYING = "retrying"
    SUCCESS  = "success"
    FAILED   = "failed"


class MessageRole(enum.Enum):
    """
    Sender of a message within a conversation.
    Mirrors the role field expected by the LLM chat completions API.
    """
    USER      = "user"
    ASSISTANT = "assistant"



# Tables


class User(Base):
    """
    Platform account. The id is the Clerk user ID, not a generated UUID.
    User records are created by the Clerk webhook on first sign-in.
    No email or name is stored here — those live in Clerk.
    """
    __tablename__ = "users"

    id            = Column(String, primary_key=True)
    createdAt     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    repositories  = relationship("Repository", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Repository(Base):
    """
    A GitHub repository submitted by a user for indexing.

    Only fields that serve a concrete purpose in the pipeline are stored:
      - githubUrl / repoName / repoOwner / defaultBranch  : GitHub API calls
      - language                                           : selects LangChain splitter
      - description                                        : prepended to LLM system prompt
      - topics                                             : pre-filters vector search by tag
      - isPrivate                                          : determines whether a GitHub token is required

    Fields excluded intentionally: stars, license, sizeKb, isArchived,
    repoCreatedAt, repoUpdatedAt — none of these affect chunking or retrieval.

    Unique constraint on (userId, githubUrl) prevents a user from submitting
    the same repo twice. Different users may index the same repo independently.
    """
    __tablename__ = "repositories"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId        = Column(String, ForeignKey("users.id"), nullable=False)

    githubUrl     = Column(String, nullable=False)
    repoName      = Column(String, nullable=True)
    repoOwner     = Column(String, nullable=True)
    defaultBranch = Column(String, nullable=True)

    language      = Column(String, nullable=True)
    description   = Column(String, nullable=True)
    topics        = Column(ARRAY(String), nullable=True)
    isPrivate     = Column(Boolean, default=False, nullable=False)

    status        = Column(
        Enum(RepoStatus, name="repo_status_enum"),
        default=RepoStatus.PENDING,
        nullable=False
    )

    createdAt     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user          = relationship("User", back_populates="repositories")
    tasks         = relationship("WorkerTask", back_populates="repo")
    conversations = relationship("Conversation", back_populates="repo")

    __table_args__ = (
        UniqueConstraint("userId", "githubUrl", name="uq_user_repo_url"),
        # queried on every dashboard load
        Index("ix_repositories_userId", "userId"),
        # queried by the worker poller and status endpoint
        Index("ix_repositories_status", "status"),
        # queried when selecting the LangChain splitter
        Index("ix_repositories_language", "language"),
    )


class WorkerTask(Base):
    """
    Tracks a single ARQ background job for one repository.

    One row is created per job dispatch. If a job is retried, attempts
    increments in place rather than creating a new row — the history
    is intentionally kept flat for simplicity.

    result stores a JSON summary of what the job produced, e.g.:
        {"files_processed": 18, "chunks_created": 142, "vectors_stored": 142}

    errorType stores the Python exception class name (e.g. "HTTPStatusError")
    so failures can be grouped and monitored without parsing errorMessage.
    """
    __tablename__ = "worker_tasks"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repoId       = Column(String, ForeignKey("repositories.id"), nullable=False)

    taskType     = Column(Enum(TaskType, name="task_type_enum"), nullable=False)
    status       = Column(
        Enum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.PENDING,
        nullable=False
    )

    # wall-clock timing for performance monitoring and stuck-job detection
    startedAt    = Column(DateTime(timezone=True), nullable=True)
    completedAt  = Column(DateTime(timezone=True), nullable=True)

    attempts     = Column(Integer, default=0, nullable=False)
    maxAttempts  = Column(Integer, default=3, nullable=False)

    errorMessage = Column(Text, nullable=True)
    errorType    = Column(String, nullable=True)
    result       = Column(JSON, nullable=True)

    createdAt    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    repo         = relationship("Repository", back_populates="tasks")

    __table_args__ = (
        Index("ix_worker_tasks_repoId", "repoId"),
        Index("ix_worker_tasks_status", "status"),
    )


class WebhookEvent(Base):
    """
    Raw ingestion log for incoming GitHub webhook payloads.

    Every webhook is written here immediately on receipt, before any
    processing occurs. This gives a reliable audit trail and allows
    failed events to be replayed.

    repoId is nullable because the repository may not yet exist in the
    database at the time the event arrives (e.g. a push before first index).

    status transitions: pending -> processed | failed
    """
    __tablename__ = "webhook_events"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    eventType    = Column(String, nullable=False)
    repoId       = Column(String, ForeignKey("repositories.id"), nullable=True)
    status       = Column(String, default="pending", nullable=False)
    payload      = Column(JSON, nullable=False)
    processedAt  = Column(DateTime(timezone=True), nullable=True)
    errorMessage = Column(Text, nullable=True)
    createdAt    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Conversation(Base):
    """
    A chat session between one user and one repository.

    A new conversation is created each time the user starts a fresh chat.
    All messages within a session are loaded and passed to the LLM on each
    turn to maintain context across questions.
    """
    __tablename__ = "conversations"

    id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId    = Column(String, ForeignKey("users.id"), nullable=False)
    repoId    = Column(String, ForeignKey("repositories.id"), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user      = relationship("User", back_populates="conversations")
    repo      = relationship("Repository", back_populates="conversations")
    messages  = relationship("Message", back_populates="conversation")


class Message(Base):
    """
    A single turn within a conversation.

    role follows the LLM API convention: "user" for developer input,
    "assistant" for generated responses.

    sourcePaths records which file paths were retrieved from the vector
    store and injected into the prompt for this response. Stored so the
    frontend can render source attribution alongside the answer.
    Null on user messages.
    """
    __tablename__ = "messages"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversationId = Column(String, ForeignKey("conversations.id"), nullable=False)
    role           = Column(Enum(MessageRole, name="message_role_enum"), nullable=False)
    content        = Column(Text, nullable=False)
    sourcePaths    = Column(ARRAY(String), nullable=True)
    createdAt      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation   = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversationId", "conversationId"),
    )
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)