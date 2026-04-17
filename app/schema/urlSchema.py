from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from typing import Optional
import re
"""Schema for URL validation and processing"""
class TrustedGitHubRepoLink(BaseModel):
    url: HttpUrl
