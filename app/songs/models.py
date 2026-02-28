import uuid
from datetime import datetime
from typing import List
from typing import Optional

from sqlmodel import Enum
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel


# --- Association table for many-to-many ---
class SourceAuthorLink(SQLModel, table=True):
    source_id: uuid.UUID = Field(foreign_key="source.id", primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True)


class SourceType(str, Enum):
    book = "book"
    cd = "cd"
    lp = "lp"
    archive = "archive"


# --- Person model ---
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

    # many-to-many relationship
    sources: List["Source"] = Relationship(
        back_populates="authors", link_model=SourceAuthorLink
    )

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Person(name={self.name}, surname={self.surname})"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


# --- Source model ---
class Source(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: str
    year: Optional[int]
    type: Optional[SourceType]
    public: bool = Field(default=False, nullable=False)

    # many-to-many relationship
    authors: List[Person] = Relationship(
        back_populates="sources", link_model=SourceAuthorLink
    )
    transcribed_by: Optional[str] = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Source(title={self.title}, year={self.year})"

    @classmethod
    def from_dict(
        cls,
        data: dict,
        session: Optional[Session] = None,
        existing_source: "Source" = None,
    ) -> "Source":
        """
        Create or update a Source from a metadata dict.
        - `existing_source`: if provided, updates that Source, otherwise creates new.
        - `data`: expects keys like 'title', 'type', 'transcribed_by', 'public', 'authors' (list of names)
        """
        source = existing_source or cls()

        # Basic fields
        source.title = data.get("title")
        source.type = data.get("type")
        source.transcribed_by = data.get("transcribed_by")
        source.public = data.get("public", False)  # <- automatically read public field

        # Handle authors list
        authors_names: List[str] = data.get("authors", [])
        if session:
            from .models import Person  # avoid circular imports

            source.authors = []  # reset authors
            for name in authors_names:
                # split name into first/last (naive)
                parts = name.strip().split(maxsplit=1)
                first = parts[0]
                last = parts[1] if len(parts) > 1 else None
                # find or create Person
                person = session.exec(
                    select(Person).where(Person.name == first, Person.surname == last)
                ).first()
                if not person:
                    person = Person(name=first, surname=last)
                    session.add(person)
                    session.commit()
                source.authors.append(person)

        return source


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
    transcribed_by: Optional[str] = None

    recorded_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="person.id")
    recorded_by: Optional["Person"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Song.recorded_by_id==Person.id",
            "lazy": "joined",
        }
    )

    @classmethod
    def from_dict(
        cls,
        data: dict,
        source: "Source",
        lytex: str,
        verses: str,
        recorded_by: "Person",
    ):
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
        for key in data:
            if hasattr(self, key):
                value = data[key]
                if isinstance(value, str) and value.strip() == "":
                    value = None  # Convert empty strings to None
                setattr(self, key, value)
