from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str
    github_api_key: str
    clerk_webhook_secret: str
    jwt_publik_key: str
    clerk_secret_key: str
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64
    embedding_max_input_chars: int = 12000
    clone_base_dir: str 
    authorized_parties: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()