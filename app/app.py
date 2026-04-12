from fastapi import FastAPI
from app.models.users import create_db_and_tables
from contextlib import asynccontextmanager
from app.router.webhook_router import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(webhook_router, prefix="/api/webhook", tags=["webhook"])


