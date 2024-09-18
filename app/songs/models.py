import uuid
from typing import Optional

from sqlmodel import Enum
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel


class SourceType(str, Enum):
    book = "book"
    cd = "cd"
    lp = "lp"
    archive = "archive"


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
    note: Optional[str] = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Person(name={self.name}, surname={self.surname})"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Source(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: Optional[str] = Field(..., nullable=False)
    year: Optional[int]
    type: Optional[SourceType]
    author_id: Optional[uuid.UUID] = Field(default=None, foreign_key="person.id")
    author: Optional["Person"] = Relationship()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Source(title={self.title}, year={self.year})"

    @classmethod
    def from_dict(cls, data: dict, author: "Person"):
        return cls(**data, author=author)


class Song(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: Optional[str] = Field(..., nullable=False)
    lytex: Optional[str]
    verses: Optional[str]
    source_id: Optional[uuid.UUID] = Field(default=None, foreign_key="source.id")
    source: Optional["Source"] = Relationship()
    signature: Optional[str]
    page: Optional[int]
    number: Optional[int]
    tempo: Optional[int]
    type: Optional[str]
    year: Optional[int]
    location: Optional[str]

    recorded_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="person.id")
    #    recorded_person_id: Optional[uuid.UUID] = Field(default=None, foreign_key="person.id")
    recorded_by: Optional["Person"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Song.recorded_by_id==Person.id",
            "lazy": "joined",
        }
    )
    #    recorded_person: Optional["Person"] = Relationship(
    #        sa_relationship_kwargs={"primaryjoin": "Song.recorded_person_id==Person.id", "lazy": "joined"}
    #    )

    @classmethod
    def from_dict(
        cls,
        data: dict,
        source: "Source",
        lytex: str,
        verses: str,
        recorded_by: "Person",
    ):
        print(data)
        return cls(
            **data, source=source, lytex=lytex, verses=verses, recorded_by=recorded_by
        )

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Song(title={self.title})"
