import uuid
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional


class Person(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    name: str
    surname: str
    alias: Optional[str] = None
    born: Optional[int] = None
    died: Optional[int] = None
    location: Optional[str] = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Person(name={self.name}, surname={self.surname})"


class Source(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: str = Field(..., nullable=False)
    year: int
    author_id: Optional[uuid.UUID] = Field(default=None, foreign_key="person.id")
    author: Optional["Person"] = Relationship()


class Song(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: str = Field(..., nullable=False)
    source_id: Optional[uuid.UUID] = Field(default=None, foreign_key="source.id")
    source: Optional["Source"] = Relationship()
