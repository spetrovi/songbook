from sqlmodel import create_engine
from sqlmodel import Session
from sqlmodel import SQLModel

# from app.users.models import User
# from app.songbooks.models import Songbook

# Define the database URL (adjust accordingly)
DATABASE_URL = "sqlite:///database.db"
# LIBRARY_URL = "sqlite:///app/songs/library.db"

# Create the SQLAlchemy engines
engine = create_engine(DATABASE_URL)
# library_engine = create_engine(LIBRARY_URL)

SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)


def yield_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
