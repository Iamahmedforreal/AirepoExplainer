import httpx
from urllib.parse import urlparse
import re


async def validate_github_repo_url(url: str) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    if parsed.netloc.lower() != "github.com":
        raise ValueError("URL must be a GitHub repository URL")
    if parsed.query:
        raise ValueError("URL must not contain query parameters")
    if parsed.fragment:
        raise ValueError("URL must not contain fragments")
    if not re.fullmatch(r"/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/?", parsed.path):
        raise ValueError("URL must be exactly: https://github.com/owner/repo")


    return True


