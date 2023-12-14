from sqlmodel import create_engine
from sqlmodel import Session
from sqlmodel import SQLModel

# Define the database URL (adjust accordingly)
DATABASE_URL = "sqlite:///database.db"
LIBRARY_URL = "sqlite:///app/songs/library.db"

# Create the SQLAlchemy engines
engine = create_engine(DATABASE_URL)
library_engine = create_engine(LIBRARY_URL)

SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)


def get_library_session():
    return Session(library_engine)
