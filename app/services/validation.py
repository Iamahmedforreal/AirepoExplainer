import httpx

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