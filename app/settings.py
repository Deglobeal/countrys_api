from pydantic import BaseSettings


class Settings(BaseSettings):
database_url: str
port: int = 8000
timeout_seconds: int = 15
cache_path: str = "cache/summary.png"


class Config:
env_file = ".env"


settings = Settings()