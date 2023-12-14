import uuid

from sqlmodel import Field
from sqlmodel import SQLModel

from . import security
from . import validators
from app.db import get_session


# Define the User model
class User(SQLModel, table=True):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(..., unique=True, nullable=False)
    password: str

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
    def create_user(email, password=None):
        with get_session() as session:
            if session.query(User).where(User.email == email).all():
                raise Exception("Email already registered")
            valid, msg, email = validators._validate_email(email)
            if not valid:
                raise Exception(f"Invalid email: {msg}")
            user = User(email=email)
            user.set_password(password)
            session.add(user)
            session.commit()

    @staticmethod
    def get_by_email(email):
        with get_session() as session:
            return session.query(User).where(User.email == email).one()
