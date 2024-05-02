import uuid
from typing import List
from typing import Optional

from sqlalchemy.exc import NoResultFound
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import select
from sqlmodel import SQLModel

import app.users.models as UserModel
from app.songs.models import Song


class Songbook(SQLModel, table=True):
    songbook_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True
    )
    user_id: uuid.UUID = Field(default=None, foreign_key="user.user_id")
    title: str = Field(default="Untitled")
    description: str = Field(default="No description")
    entries: List["Entry"] = Relationship()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Songbook(title={self.title}, user_id={self.user_id})"

    @staticmethod
    def get_by_user_songbook_id(user_id, songbook_id, session):
        return session.exec(
            select(Songbook)
            .where(Songbook.user_id == user_id)
            .where(Songbook.songbook_id == songbook_id)
        ).one()

    @staticmethod
    def create_songbook(user_id, session):
        if not session.exec(
            select(UserModel.User).where(UserModel.User.user_id == user_id)
        ).first():
            raise Exception("User doesn't exists")
        songbook = Songbook(user_id=user_id)
        session.add(songbook)
        session.commit()
        session.refresh(songbook)
        return songbook

    @staticmethod
    def delete_songbook(user_id, songbook_id, session):
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
    def add_song(songbook_id, song_id, session):
        if not session.exec(select(Song).where(Song.id == song_id)).first():
            raise Exception("Song doesn't exists")
        try:
            songbook = session.exec(
                select(Songbook).where(Songbook.songbook_id == songbook_id)
            ).one()
        except NoResultFound:
            raise Exception("Songbook doesn't exists")
        if session.exec(
            select(Entry)
            .where(Entry.songbook_id == songbook_id)
            .where(Entry.song_id == song_id)
        ).first():
            raise Exception("Duplicit entry")
        entry = Entry(
            songbook_id=songbook_id, song_id=song_id, order=len(songbook.entries)
        )
        session.add(entry)
        session.commit()

    @staticmethod
    def reorder_songs(song_list, songbook_id, session):
        filtered_list = list(filter(lambda tpl: "songbook_id" not in tpl, song_list))

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
    def get_songs(songbook_id, session):
        statement = select(Entry).where(Entry.songbook_id == songbook_id)
        entries = session.exec(statement).all()
        sorted_entries = sorted(entries, key=lambda entry: entry.order)
        return [entry.song for entry in sorted_entries]

    @staticmethod
    def remove_song(songbook_id, song_id, session):
        statement = (
            select(Entry)
            .where(Entry.songbook_id == songbook_id)
            .where(Entry.song_id == song_id)
        )
        entry = session.exec(statement).one()
        session.delete(entry)
        session.commit()
        songbook = session.exec(
            select(Songbook).where(Songbook.songbook_id == entry.songbook_id)
        ).one()
        session.refresh(songbook)
        for i, elem in enumerate(songbook.entries):
            if i >= entry.order:
                elem.order -= 1
        session.commit()

    @staticmethod
    def delete_entry(entry_id, session):
        statement = select(Entry).where(Entry.id == entry_id)
        entry = session.exec(statement).one()
        session.delete(entry)
        session.commit()
        songbook = session.exec(
            select(Songbook).where(Songbook.songbook_id == entry.songbook_id)
        ).one()
        session.refresh(songbook)
        for i, elem in enumerate(songbook.entries):
            if i >= entry.order:
                elem.order -= 1
        session.commit()
