from fastapi import FastAPI
from app.models.users import create_db_and_tables
from contextlib import asynccontextmanager
from app.router.webhook_router import router 
from app.models.users import Base
from app.models.webhook import WebhookEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(router, prefix="/api")

