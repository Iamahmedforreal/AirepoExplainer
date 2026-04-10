from fastapi import FastAPI
from app.models.users import create_db_and_tables
from app.router.authRouter import router as auth_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


