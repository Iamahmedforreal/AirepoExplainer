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




class RepoStatus(int, enum.Enum):
    PENDING  = 1
    INDEXING = 2
    INDEXED  = 3
    FAILED   = 4
    OUTDATED = 5


class TaskType(int, enum.Enum):
    """
    Granularity of a worker job.
    FULL_PIPELINE runs all stages in a single ARQ task.
    Individual types are reserved for partial re-runs (e.g. re-embed only).
    """
    FULL_PIPELINE = 1
    CLONE         = 2
    CHUNK         = 3
    EMBED         = 4
    PARSING       = 5


class TaskStatus(int, enum.Enum):
    """
    Execution state of a single WorkerTask row.
    RETRYING means attempts > 1 but < maxAttempts and job is back in the queue.
    """
    PENDING  = 1
    RUNNING  = 2
    RETRYING = 3
    SUCCESS  = 4
    FAILED   = 5


class MessageRole(int, enum.Enum):
    """
    Sender of a message within a conversation.
    Mirrors the role field expected by the LLM chat completions API.
    """
    USER      = 1
    ASSISTANT = 2


# Database Lookup Tables for Star-Schema Normalization

class RepoStatusLookup(Base):
    __tablename__ = "repo_statuses"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class TaskTypeLookup(Base):
    __tablename__ = "task_types"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class TaskStatusLookup(Base):
    __tablename__ = "task_statuses"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class MessageRoleLookup(Base):
    __tablename__ = "message_roles"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)




# Tables


class User(Base):
    """
    user table from clerk
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
    """
    __tablename__ = "repositories"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId        = Column(String, ForeignKey("users.id"), nullable=False)

    githubUrl     = Column(String, nullable=False)
    defaultBranch = Column(String, nullable=True)

    language      = Column(String, nullable=True)
    description   = Column(String, nullable=True)
    topics        = Column(ARRAY(String), nullable=True)
    isPrivate     = Column(Boolean, default=False, nullable=False)

    statusId      = Column(
        Integer,
        ForeignKey("repo_statuses.id"),
        default=RepoStatus.PENDING.value,
        nullable=False
    )
    status        = relationship("RepoStatusLookup", lazy="joined")

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
        Index("ix_repositories_status", "statusId"),
        # queried when selecting the LangChain splitter
        Index("ix_repositories_language", "language"),
    )


class WorkerTask(Base):
    """
    Tracks one background job stage for one repository.

    The unique constraint on (repoId, taskTypeId) guarantees that each
    repository can have only one row for a stage such as CLONE or PARSING.
    Workers insert directly and let PostgreSQL reject duplicates.

    result stores a JSON summary of what the job produced, e.g.:
        {"files_processed": 18, "chunks_created": 142, "vectors_stored": 142}

    errorType stores the Python exception class name (e.g. "HTTPStatusError")
    so failures can be grouped and monitored without parsing errorMessage.
    """
    __tablename__ = "worker_tasks"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repoId       = Column(String, ForeignKey("repositories.id"), nullable=False)

    taskTypeId   = Column(Integer, ForeignKey("task_types.id"), nullable=False)
    statusId     = Column(
        Integer,
        ForeignKey("task_statuses.id"),
        default=TaskStatus.PENDING.value,
        nullable=False
    )

    taskType     = relationship("TaskTypeLookup", lazy="joined")
    status       = relationship("TaskStatusLookup", lazy="joined")

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
        UniqueConstraint("repoId", "taskTypeId", name="uq_worker_tasks_repo_type"),
        Index("ix_worker_tasks_repoId", "repoId"),
        Index("ix_worker_tasks_status", "statusId"),
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
    roleId         = Column(Integer, ForeignKey("message_roles.id"), nullable=False)
    role           = relationship("MessageRoleLookup", lazy="joined")
    content        = Column(Text, nullable=False)
    sourcePaths    = Column(ARRAY(String), nullable=True)
    createdAt      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation   = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversationId", "conversationId"),
    )


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repoId = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False)  # Relative path, e.g. "app/services/urlService.py"
    type = Column(String, nullable=False)  # "module" | "class" | "method" | "function" | "interface" | "type"
    name = Column(String, nullable=False)  # e.g., "save_repo"
    fullName = Column(String, nullable=False)  # Fully qualified name, e.g. "app.services.urlService.save_repo"
    startLine = Column(Integer, nullable=False)
    endLine = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    parentChunkId = Column(String, ForeignKey("code_chunks.id", ondelete="CASCADE"), nullable=True)

    repo = relationship("Repository")
    parent = relationship("CodeChunk", remote_side=[id], backref="children")

    __table_args__ = (
        Index("ix_code_chunks_repoId", "repoId"),
        Index("ix_code_chunks_path", "path"),
        Index("ix_code_chunks_type", "type"),
        Index("ix_code_chunks_name", "name"),
    )


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed the lookup tables on application startup
    from app.models.db import async_session
    from sqlalchemy.dialects.postgresql import insert

    async with async_session() as session:
        async with session.begin():
            # Seed repo_statuses
            for r_status in RepoStatus:
                stmt = (
                    insert(RepoStatusLookup)
                    .values(id=r_status.value, name=r_status.name.lower())
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                await session.execute(stmt)

            # Seed task_types
            for t_type in TaskType:
                stmt = (
                    insert(TaskTypeLookup)
                    .values(id=t_type.value, name=t_type.name.lower())
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                await session.execute(stmt)

            # Seed task_statuses
            for t_status in TaskStatus:
                stmt = (
                    insert(TaskStatusLookup)
                    .values(id=t_status.value, name=t_status.name.lower())
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                await session.execute(stmt)

            # Seed message_roles
            for m_role in MessageRole:
                stmt = (
                    insert(MessageRoleLookup)
                    .values(id=m_role.value, name=m_role.name.lower())
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                await session.execute(stmt)
