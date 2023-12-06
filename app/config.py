from pydantic import Field
from pydantic import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = Path(__file__).resolve().parent / "templates"
    secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
