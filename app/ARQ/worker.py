from arq.connections import RedisSettings
from app.ARQ.task import clone_repository
from app.config.app_config import settings


async def startup(ctx):
    print("Worker starting up...")

async def shutdown(ctx):
    print("Worker shutting down...")

class WorkerSettings:
    functions = [clone_repository]
    redis_settings = RedisSettings(host="localhost", port=6379)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 5
    job_timeout = 300  