import os
import shutil
from git import Repo
from app.config.app_config import settings



def clone_repo(owner: str, repo_name: str, github_url: str) -> str:
    """ clones repo to local disk using GitPython.
    Returns the absolute path to the cloned directory.
    """
    dest = os.path.join(settings.clone_base_dir, owner, repo_name)

    # Fresh clone every time
    if os.path.exists(dest):
        shutil.rmtree(dest)

    os.makedirs(dest, exist_ok=True)
    Repo.clone_from(github_url, dest, depth=1)

    
    return dest