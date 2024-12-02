import sys
from pathlib import Path

from pydantic import Field
from pydantic import ValidationError
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = Path(__file__).resolve().parent / "templates"
    secret_key: str = Field(...)
    register_enabled: bool = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    session_duration: int = Field(default=86400)
    database_url: str = Field(default=None)

    class Config:
        env_file = ".env"

    @validator("database_url", pre=True)
    def fix_postgres_prefix(cls, database_url):
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        if database_url is None:
            raise ValueError("Please set DATABASE_URL")
        return database_url


def get_settings():
    try:
        return Settings()
    except ValidationError as e:
        print(f"Couldn't configure Settings: \n{e}")
        sys.exit()
