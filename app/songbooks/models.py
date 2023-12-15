import uuid

from sqlmodel import Field
from sqlmodel import SQLModel

from app.db import get_session
from app.users.models import User


# Define the User model
class Songbook(SQLModel, table=True):
    songbook_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    user_id: uuid.UUID = Field(default=None, foreign_key="user.user_id")
    title: str = Field(default="Untitled")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Songbook(title={self.title}, user_id={self.user_id})"

    @staticmethod
    def create_songbook(songbook_id, user_id):
        with get_session() as session:
            if not session.query(User).where(User.user_id == user_id).all():
                raise Exception("User doesn't exists")
            songbook = Songbook(songbook_id=songbook_id, user_id=user_id)
            session.add(songbook)
            session.commit()

    @staticmethod
    def get_by_user_id(user_id):
        with get_session() as session:
            return session.query(Songbook).where(Songbook.user_id == user_id).one()

    @staticmethod
    def get_by_songbook_id(songbook_id):
        with get_session() as session:
            return (
                session.query(Songbook).where(Songbook.songbook_id == songbook_id).one()
            )
