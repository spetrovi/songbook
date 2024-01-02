import uuid

from sqlmodel import Field
from sqlmodel import select
from sqlmodel import SQLModel

from app.db import get_library_session
from app.db import get_session
from app.songs.models import Song
from app.users.models import User


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


class Entry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    songbook_id: uuid.UUID = Field(default=None, foreign_key="songbook.songbook_id")
    song_id: uuid.UUID = Field(default=None, foreign_key="song.id")

    # TODO add check if we're not adding duplicit entries
    @staticmethod
    def add_song(songbook_id, song_id):
        with get_library_session() as session:
            if not session.exec(select(Song).where(Song.id == song_id)).one():
                raise Exception("Song doesn't exists")

        with get_session() as session:
            if not session.exec(
                select(Songbook).where(Songbook.songbook_id == songbook_id)
            ).one():
                raise Exception("Songbook doesn't exists")
            entry = Entry(songbook_id=songbook_id, song_id=song_id)
            session.add(entry)
            session.commit()

    @staticmethod
    def get_songs(songbook_id):
        # get song ids from the ledger
        with get_session() as session:
            statement = select(Entry).where(Entry.songbook_id == songbook_id)
        entries = session.exec(statement).all()
        song_ids = [entry.song_id for entry in entries]

        # get actual songs
        with get_library_session() as session:
            statement = select(Song).where(Song.id.in_(song_ids))
            songs = session.exec(statement).all()
        return songs
