import uuid

from sqlmodel import Field
from sqlmodel import select
from sqlmodel import SQLModel

import app.users.models
from app.db import get_library_session
from app.db import get_session
from app.songs.models import Song


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
            if (
                not session.query(app.users.models.User)
                .where(app.users.models.User.user_id == user_id)
                .all()
            ):
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

    @staticmethod
    def get_by_user_songbook_id(user_id, songbook_id):
        with get_session() as session:
            statement = (
                select(Songbook)
                .where(Songbook.user_id == user_id)
                .where(Songbook.songbook_id == songbook_id)
            )
            songbook = session.exec(statement).one()
            return songbook

    @staticmethod
    def delete_songbook(songbook_id):
        Entry.remove_songbook(songbook_id)
        with get_session() as session:
            #            if not session.query(Songbook).where(Songbook.songbook_id == songbook_id).one():
            #                raise exceptions.SongbookDoesntExistException("Songbook doesn't exist")
            statement = select(Songbook).where(Songbook.songbook_id == songbook_id)
            songbook = session.exec(statement).one()
            session.delete(songbook)
            session.commit()


class Entry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    songbook_id: uuid.UUID = Field(default=None, foreign_key="songbook.songbook_id")
    song_id: uuid.UUID = Field(default=None, foreign_key="song.id")
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
        with get_library_session() as session:
            if not session.exec(select(Song).where(Song.id == song_id)).one():
                raise Exception("Song doesn't exists")

        with get_session() as session:
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
    def reorder_songs(song_list):
        entry_ids = []
        songbook_id = list(filter(lambda tpl: "songbook_id" in tpl, song_list))[0][1]
        filtered_list = list(filter(lambda tpl: "songbook_id" not in tpl, song_list))
        for index, (first_id, second_id) in enumerate(filtered_list):
            with get_session() as session:
                statement = (
                    select(Entry)
                    .where(Entry.songbook_id == songbook_id)
                    .where(Entry.song_id == first_id)
                )
                entry = session.exec(statement).one()
                entry.order = index
                session.add(entry)
                session.commit()
                entry_ids.append(entry.id)
        return entry_ids

    def get_song_by_entry_id(entry_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.id == entry_id)
            entry = session.exec(statement).one()
            with get_library_session() as session:
                statement = select(Song).where(Song.id == entry.song_id)
                return session.exec(statement).one()

    @staticmethod
    def get_songs(songbook_id):
        with get_session() as session:
            statement = select(Entry).where(Entry.songbook_id == songbook_id)
        entries = session.exec(statement).all()
        song_ids = [(entry.order, entry.id) for entry in entries]
        sorted_entry_ids = sorted(song_ids, key=lambda x: x[0])
        return [
            Entry.get_song_by_entry_id(entry_id) for (_, entry_id) in sorted_entry_ids
        ]

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
