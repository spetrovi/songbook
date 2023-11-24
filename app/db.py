from sqlmodel import create_engine
from sqlmodel import SQLModel
from sqlmodel import Session
from .users import models

# Define the database URL (adjust accordingly)
DATABASE_URL = "sqlite:///database.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def get_session():
    return Session(engine)
