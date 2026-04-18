from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl, field_validator

class TrustedGitHubRepoLink(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def must_be_github(cls, v: HttpUrl) -> HttpUrl:
        if v.host != "github.com":
            raise ValueError("URL must be a GitHub repository URL")
        return v