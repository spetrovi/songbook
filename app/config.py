from pathlib import Path

from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = Path(__file__).resolve().parent / "templates"
    secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    session_duration: int = Field(default=86400)

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
