from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    clerk_webhook_secret: str

    class Config:
        env_file = ".env"

settings = Settings()