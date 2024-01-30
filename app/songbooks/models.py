import uuid
from typing import List
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import select
from sqlmodel import SQLModel

from app.db import get_session
from app.songs.models import Song
from app.users.models import User


class Songbook(SQLModel, table=True):
    songbook_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    user_id: uuid.UUID = Field(default=None, foreign_key="user.user_id")
    title: str = Field(default="Untitled")

    entries: List["Entry"] = Relationship()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Songbook(title={self.title}, user_id={self.user_id})"

    @staticmethod
    def get_by_user_songbook_id(user_id, songbook_id):
        with get_session() as session:
            return session.exec(
                select(Songbook)
                .where(Songbook.user_id == user_id)
                .where(Songbook.songbook_id == songbook_id)
            ).one()

    @staticmethod
    def create_songbook(user_id):
        with get_session() as session:
            if not session.exec(select(User).where(User.user_id == user_id)).first():
                raise Exception("User doesn't exists")
            songbook = Songbook(user_id=user_id)
            session.add(songbook)
            session.commit()
            return songbook.songbook_id

    @staticmethod
    def delete_songbook(user_id, songbook_id):
        with get_session() as session:
            statement = (
                select(Songbook)
                .where(Songbook.songbook_id == songbook_id)
                .where(Songbook.user_id == user_id)
            )
            songbook = session.exec(statement).one()

            for entry in songbook.entries:
                session.delete(entry)

            session.delete(songbook)
            session.commit()


class Entry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    songbook_id: uuid.UUID = Field(default=None, foreign_key="songbook.songbook_id")
    song_id: uuid.UUID = Field(default=None, foreign_key="song.id")
    song: Optional["Song"] = Relationship()
    order: int = Field(default=None)

    @staticmethod
    def count_songs(songbook_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.songbook_id == songbook_id)
            result = session.exec(statement).all()
            return len(result)

    # TODO add check if we're not adding duplicit entries
    @staticmethod
    def add_song(songbook_id, song_id):
        with get_session() as session:
            if not session.exec(select(Song).where(Song.id == song_id)).one():
                raise Exception("Song doesn't exists")
            if not session.exec(
                select(Songbook).where(Songbook.songbook_id == songbook_id)
            ).one():
                raise Exception("Songbook doesn't exists")
            if not session.exec(
                select(Entry)
                .where(Entry.songbook_id == songbook_id)
                .where(Entry.song_id == song_id)
            ).first():
                entry = Entry(
                    songbook_id=songbook_id,
                    song_id=song_id,
                    order=Entry.count_songs(songbook_id),
                )
                session.add(entry)
                session.commit()

    @staticmethod
    def reorder_songs(song_list, songbook_id):
        filtered_list = list(filter(lambda tpl: "songbook_id" not in tpl, song_list))
        with get_session() as session:
            entries = session.exec(
                select(Entry).where(Entry.songbook_id == songbook_id)
            ).all()
            for index, (first_id, second_id) in enumerate(filtered_list):
                statement = (
                    select(Entry)
                    .where(Entry.songbook_id == songbook_id)
                    .where(Entry.song_id == first_id)
                )
                entry = session.exec(statement).one()
                entry.order = index
                session.add(entry)
                session.commit()
            sorted_entries = sorted(entries, key=lambda entry: entry.order)
            return [entry.song for entry in sorted_entries]

    @staticmethod
    def get_songs(songbook_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.songbook_id == songbook_id)
            entries = session.exec(statement).all()
            sorted_entries = sorted(entries, key=lambda entry: entry.order)
            return [entry.song for entry in sorted_entries]

    @staticmethod
    def remove_song(songbook_id, song_id):
        with get_session() as session:
            statement = (
                select(Entry)
                .where(Entry.songbook_id == songbook_id)
                .where(Entry.song_id == song_id)
            )
            entry = session.exec(statement).one()
            session.delete(entry)
            session.commit()
        return 1

    @staticmethod
    def remove_songbook(songbook_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.songbook_id == songbook_id)
            entries = session.exec(statement).all()
            for entry in entries:
                session.delete(entry)
            session.commit()

    @staticmethod
    def delete_entry(entry_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.id == entry_id)
            entry = session.exec(statement).one()
            session.delete(entry)
            session.commit()
