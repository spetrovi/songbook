import os

from sqlmodel import create_engine
from sqlmodel import Session


# from app.users.models import User
# from app.songbooks.models import Songbook


# When run the container should be initialized with the following environment variables:
# DATABASE_SCHEMA: "sqlite" or "postgresql"
# If you choose postgresql, you should also set the following environment variables:
# DATABASE_USER: the username for the database
# DATABASE_PASSWORD: the password for the database
# DATABASE_NAME: the name of the database
# DATABASE_PORT: the port for the database (optional, default is 5432)
# DATABASE_HOST: the host for the database (optional, default is "localhost")

# Define the database URL (adjust accordingly)
if os.environ.get("DATABASE_SCHEMA") != "sqlite" and os.environ.get("DATABASE_SCHEMA") != "postgresql":
    raise ValueError("DATABASE_SCHEMA must be set to 'sqlite' or 'postgresql'")
if os.environ.get("DATABASE_SCHEMA") == "sqlite":
    DATABASE_URL = "sqlite:///database.db"
# LIBRARY_URL = "sqlite:///app/songs/library.db"
if os.environ.get("DATABASE_SCHEMA") == "postgresql":
    for var in ["DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME"]:
        if not os.environ.get(var):
            raise ValueError(f"{var} must be set when using postgresql")
    user = os.environ.get("DATABASE_USER")
    password = os.environ.get("DATABASE_PASSWORD")
    database_name = os.environ.get("DATABASE_NAME")
    port = os.environ.get("DATABASE_PORT", "5432")
    host = os.environ.get("DATABASE_HOST", "localhost")
    DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{database_name}".format(
        user=user, password=password, host=host, port=port, database_name=database_name
    )

# Create the SQLAlchemy engines
engine = create_engine(DATABASE_URL)
# library_engine = create_engine(LIBRARY_URL)


def get_session():
    return Session(engine)


def yield_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
