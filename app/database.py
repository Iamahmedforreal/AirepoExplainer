from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql+asyncpg" , "postgresql+psycopg2")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

sync_engine = create_engine(DATABASE_URL)
SyncSession = sessionmaker(bind=sync_engine)

