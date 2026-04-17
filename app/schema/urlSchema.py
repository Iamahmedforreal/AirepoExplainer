from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from typing import Optional
import re

"""Schema for validating GitHub repository URLs. The URL must be in the format: https://github.com/user/repo"""
class TrustedGitHubRepoLink(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def must_be_exact_repo_url(cls, v: HttpUrl) -> HttpUrl:
        # Must be exactly github.com 
        if v.host.lower() != "github.com":
            raise ValueError("Only github.com is allowed")

        # No query parameters
        if v.query:
            raise ValueError("Query parameters are not allowed")

        # No fragments
        if v.fragment:
            raise ValueError("Fragments are not allowed")

        # Must match exactly /user/repo or /user/repo/
        path = v.path

        match = re.fullmatch(r"/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?", path)
        if not match:
            raise ValueError("URL must be exactly in format: https://github.com/user/repo")

        return v