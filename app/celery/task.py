import os
import shutil
from git import GitCommandError, Repo
from app.celery.celery import app


@app.task(bind=True, name="clone_repository", max_retries=3, default_retry_delay=60)
def clone_repository(self, url: str, target_dir: str):
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        os.makedirs(target_dir, exist_ok=True)

        Repo.clone_from(url, target_dir)
        return {"status": "success"}

    except GitCommandError as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise self.retry(exc=e)

    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise 