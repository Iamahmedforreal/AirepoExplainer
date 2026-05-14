import os
import shutil
from git import Repo
from app.config.app_config import settings
from app.services.urlService import collect_clean_repo, read_file_contents

def clone_repo(owner: str, repo_name: str, github_url: str) -> dict:
    """Clone a repository and collect only useful source files.

    Returns:
        {
            "clone_path": str,                # absolute path to the raw clone
            "folders":    list[str],           # clean directory tree
            "files":      list[dict],          # [{"path": ..., "content": ...}, ...]
        }
    """
    dest = os.path.join(settings.clone_base_dir, owner, repo_name)

    # Fresh clone every time
    if os.path.exists(dest):
        shutil.rmtree(dest)

    os.makedirs(dest, exist_ok=True)
    Repo.clone_from(github_url, dest, depth=1)

    # Non-destructive walk — nothing on disk is deleted
    clean = collect_clean_repo(dest)
    file_contents = read_file_contents(clean["files"])

    return {
        "clone_path": dest,
        "folders":    clean["folders"],
        "files":      file_contents,
    }