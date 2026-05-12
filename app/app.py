import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.models.repo_models import create_db_and_tables, Base
from contextlib import asynccontextmanager
from app.router.urlRoute import router
from app.router.webhookRouter import router_webhook
from arq.connections import RedisSettings
from arq import create_pool


logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    await create_db_and_tables()
    app.state.redis = await create_pool(RedisSettings(host="localhost", port=6379))

    yield

    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)
redis = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    if duration > 500:
        logger.warning(f"SLOW REQUEST: {request.method} {request.url.path} {duration:.0f}ms")

    print(f"{request.method} {request.url.path} took {duration:.2f}ms")
    return response


    
# Include routers
app.include_router(router)
app.include_router(router_webhook)



