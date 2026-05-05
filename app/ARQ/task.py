import os
import asyncio
import shutil
from arq import Retry
from git import GitCommandError, Repo


async def clone_repository(ctx, url: str, target_dir: str):
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        os.makedirs(target_dir, exist_ok=True)

        await asyncio.to_thread(
           Repo.clone_from,
           url,
           target_dir,
           depth=1,
           no_single_branch=True,
           env={"GIT_TERMINAL_PROMPT": "0"},
   )
        return {"status": "success"}

    except GitCommandError as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise Retry(defer=5)  
    
    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise