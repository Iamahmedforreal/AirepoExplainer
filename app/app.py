from fastapi import FastAPI
from app.models.users import create_db_and_tables
from contextlib import asynccontextmanager
from app.models.users import Base



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)



