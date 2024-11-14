import uuid
from datetime import datetime
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


class SongEdit(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )

    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.user_id")

    modified: Optional[datetime]
    img_src_path: Optional[str] = Field(default=None)

    # lilypond stuff
    lytex: Optional[str]
    autobeamoff: Optional[bool] = Field(default=True)
    includelyrics: Optional[bool] = Field(default=False)
    time_numerator: Optional[int] = Field(default=2)
    time_denominator: Optional[int] = Field(default=4)
    key_value: Optional[str] = Field(default="c")
    key_type: Optional[str] = Field(default="major")
    tempo: Optional[str] = Field(default=None)
    tempomidi: Optional[int] = Field(default=120)
    firsttone: Optional[str] = Field(default="a")
    tones: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None)
    scorelyrics: Optional[str] = Field(default=None)
    instrument: Optional[str] = Field(default="acoustic grand")
    #    uuid = form_data.get("uuid")

    verses: Optional[str] = Field(default=None)

    # metadata
    title: Optional[str]
    signature: Optional[str]
    page: Optional[int]
    number: Optional[int]

    type: Optional[str]
    year: Optional[int]
    location: Optional[str]

    recorded_by_name: Optional[str]
    recorded_by_surname: Optional[str]

    recorded_name: Optional[str]
    recorded_surname: Optional[str]
    recorded_age: Optional[int]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"SongEdit(title={self.title})"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def update_from_dict(self, data: dict):
        """Updates an existing instance based on a dictionary."""
        for key, value in data.items():
            if value:
                if hasattr(self, key):  # Check if the attribute exists on the object
                    setattr(self, key, value)
