import sys
from pathlib import Path

from pydantic import BaseSettings
from pydantic import Field
from pydantic.error_wrappers import ValidationError


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = Path(__file__).resolve().parent / "templates"
    secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    session_duration: int = Field(default=86400)

    class Config:
        env_file = ".env"


def get_settings():
    try:
        return Settings()
    except ValidationError as e:
        print(f"Couldn't configure Settings: \n{e}")
        sys.exit()
