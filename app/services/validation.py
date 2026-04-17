import httpx
from urllib.parse import urlparse
import re

"""Service for validating URLs and checking their reachability"""
async def check_url_reachable(url: str) -> None:
    timeout = httpx.Timeout(5.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        try:
            response = await client.head(url)
        except httpx.RequestError:
            raise ValueError("URL is unreachable (network error)")

    if response.status_code >= 400:
        raise ValueError(f"URL is unreachable (status {response.status_code})")
"""This function validates that the provided URL is a well-formed GitHub repository URL and does not contain any query parameters or fragments."""

async def validate_github_repo_url(url: str) -> None:
    # Basic URL format validation
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
        raise ValueError("URL must be exactly: https://github.com/user/repo")