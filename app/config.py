from pydantic import Field
from pydantic import BaseSettings
from pathlib import Path
class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = Path(__file__).resolve().parent / "templates"
    secret_key: str = Field(...) # pydantic maps secret_key to SECRET_KEY automatically, so we dont have to do Field(..., env='SECRET_KEY')
    jwt_algorithm: str = Field(default='HS256')

    class Config:
        env_file = '.env'

def get_settings():
    return Settings()
