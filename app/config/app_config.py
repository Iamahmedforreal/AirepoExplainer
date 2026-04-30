from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str
    github_api_key: str
    clerk_webhook_secret: str
    jwt_publik_key: str
    clerk_secret_key: str = Field(..., validation_alias="CLEERK_SCERET_KEY")
    redis_url : str
    clone_base_dir: str = r"C:\Users\hp\repoAiProject\cloned_repos"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


