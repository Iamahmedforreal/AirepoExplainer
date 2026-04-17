from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from typing import Optional
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"github.com"}
"""Schema for validating URLs, ensuring they belong to allowed domains (e.g., GitHub"""
class TrustedLink(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def must_be_github(cls, v: HttpUrl) -> HttpUrl:
        host = v.host.lower()

        if host == "github.com" or host.endswith(".github.com"):
            return v

        raise ValueError("Only GitHub links are allowed")