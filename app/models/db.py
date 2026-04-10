from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Load environment variables from .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the asynchronous engine
engine = create_async_engine(DATABASE_URL , echo=True)

# Create the asynchronous session maker
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency to get the database session
async def get_db():
    async with async_session() as session:
        yield session




