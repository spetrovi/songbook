from sqlmodel import create_engine
from sqlmodel import Session

from app import config

settings = config.get_settings()
engine = create_engine(settings.database_url)


def get_session():
    return Session(engine)


def yield_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
