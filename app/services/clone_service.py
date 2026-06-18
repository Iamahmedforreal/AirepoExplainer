import os
import shutil

from git import Repo

from app.config.app_config import settings
from app.services.urlService import collect_clean_repo, read_file_contents


def clone_repo(owner: str, repo_name: str, github_url: str) -> dict:
    """Clone a repository and collect only useful source files.

    Returns:
        {
            "clone_path": str,
            "folders":    list[str],
            "files":      list[dict],  # [{"path": ..., "content": ...}, ...]
        }
    """
    dest = os.path.join(settings.clone_base_dir, owner, repo_name)

    if os.path.exists(dest):
        shutil.rmtree(dest)

    os.makedirs(dest, exist_ok=True)
    Repo.clone_from(github_url, dest, depth=1)


    return {
        "clone_path": dest,
    } 


def load_files_from_clone(clone_path: str) -> list[dict]:
    """Re-read accepted source files from an on-disk clone."""
    clean = collect_clean_repo(clone_path)
    return read_file_contents(clean["files"])
