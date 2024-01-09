import uuid

from sqlmodel import Field
from sqlmodel import select
from sqlmodel import SQLModel

import app.songbooks.models
from . import exceptions
from . import security
from . import validators
from app.db import get_session


# Define the User model
class User(SQLModel, table=True):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(..., unique=True, nullable=False)
    password: str
    is_admin: bool = Field(default=False)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"User(email={self.email}, user_id={self.user_id})"

    def verify_password(self, pw_str):
        pw_hash = self.password
        verified, _ = security.verify_hash(pw_hash, pw_str)
        return verified

    def set_password(self, pw, commit=False):
        pw_hash = security.generate_hash(pw)
        self.password = pw_hash
        if commit:
            self.save()
        return True

    @staticmethod
    def create_user(email, password=None, is_admin=False):
        with get_session() as session:
            if session.query(User).where(User.email == email).all():
                raise exceptions.UserHasAccountException("User already has an account.")
            valid, msg, email = validators._validate_email(email)
            if not valid:
                raise exceptions.InvalidEmailException(f"Invalid email: {msg}")
            user = User(email=email, is_admin=is_admin)
            user.set_password(password)
            session.add(user)
            session.commit()

    @staticmethod
    def delete_user(user_id):
        with get_session() as session:
            if not session.query(User).where(User.user_id == user_id).one():
                raise exceptions.UserDoesntExistException("User doesn't exist")
            statement = select(app.songbooks.models.Songbook).where(
                app.songbooks.models.Songbook.user_id == user_id
            )
            songbooks = session.exec(statement).all()
            for songbook in songbooks:
                app.songbooks.models.Songbook.delete_songbook(songbook.songbook_id)
            session.commit()

            statement = select(User).where(User.user_id == user_id)
            user = session.exec(statement).one()
            session.delete(user)
            session.commit()

    @staticmethod
    def get_by_email(email):
        with get_session() as session:
            return session.query(User).where(User.email == email).one()
