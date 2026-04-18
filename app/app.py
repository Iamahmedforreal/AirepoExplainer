from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.users import create_db_and_tables, Base
from contextlib import asynccontextmanager
from app.router.urlRoute import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)



