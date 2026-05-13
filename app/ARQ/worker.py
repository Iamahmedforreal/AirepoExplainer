from arq.connections import RedisSettings
from app.ARQ.task import index_repo


async def startup(ctx):
    print("ARQ worker starting up...")


async def shutdown(ctx):
    print("ARQ worker shutting down...")


class WorkerSettings:
    functions = [index_repo]
    redis_settings = RedisSettings(host="localhost", port=6379)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10       # each worker handles up to 10 repos concurrently
    job_timeout = 120   # 2 min per job (tree fetch only, no content yet)
