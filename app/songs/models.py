import uuid
from sqlmodel import Field, SQLModel, Relationship, Enum
from typing import Optional


class SourceType(str, Enum):
    book = "book"
    cd = "cd"
    lp = "lp"


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

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Source(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    title: str = Field(..., nullable=False)
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
    title: str = Field(..., nullable=False)
    lytex: Optional[str]
    verses: Optional[str]
    source_id: Optional[uuid.UUID] = Field(default=None, foreign_key="source.id")
    source: Optional["Source"] = Relationship()
    #    pdf_partial: Optional[bytes] = Column(LargeBinary, nullable=True)
    pdf_path: Optional[str] = Field(default=None)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Song(title={self.title})"
