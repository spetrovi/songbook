import json
from pathlib import Path

from sqlalchemy.exc import NoResultFound
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel

from .models import Person
from .models import Song
from .models import Source
from app.config import get_settings
from app.utils import build_song

settings = get_settings()
engine = create_engine(settings.database_url)

SQLModel.metadata.create_all(engine)


def reformat_meta(metadata):
    # Create a new dictionary without the 'record' field
    transformed_metadata = metadata.copy()
    print(transformed_metadata["source"])
    transformed_metadata["page"] = transformed_metadata["source"].pop("page", None)

    record_data = transformed_metadata.pop("record", {})

    transformed_metadata["recorded_by"] = record_data.pop("recorded_by", None)
    transformed_metadata["location"] = record_data.pop("location", None)
    transformed_metadata["year"] = record_data.pop("year", None)
    transformed_metadata["recorded_person"] = record_data.pop("source", {})
    return transformed_metadata


def make_entry(session, meta_orig, lytex_source, verses_source):
    meta = meta_orig.copy()
    source = session.exec(
        select(Source).where(Source.title == meta["source"]["title"])
    ).one()
    if "recorded_by" in meta.keys():
        name, surname = meta["recorded_by"].split(" ")
        try:
            recorded_by = session.exec(
                select(Person)
                .where(Person.name == name)
                .where(Person.surname == surname)
            ).one()
        except NoResultFound:
            recorded_by = Person(name=name, surname=surname)
            session.add(recorded_by)
    else:
        recorded_by = None
    #            recorded_person = find_person_by_dict(person_list, meta["recorded_person"])
    meta.pop("source", None)
    meta.pop("recorded_by", None)
    meta.pop("recorded_person", None)
    song = Song.from_dict(
        meta,
        source=source,
        lytex=lytex_source,
        verses=verses_source,
        recorded_by=recorded_by,
    )
    session.add(song)
    session.commit()

    return song


def update_metadata(song, meta):
    # Remove nested dictionaries
    clean_data = {
        key: value for key, value in meta.items() if not isinstance(value, dict)
    }

    # Update only top-level attributes
    updated = False
    for key, value in clean_data.items():
        try:
            if hasattr(song, key):
                current_value = getattr(song, key)
                if current_value != value:
                    updated = True
                    setattr(song, key, value)
        except Exception:
            continue
    return song, updated


#    for key, value in meta.items():
#        song[key] = value
#        if hasattr(song, key):
#            setattr(song, key, value)
#    for key, item in meta.items()
#        try:
#            song.


def find_song_by_id(db_songs_ids, target_id):
    for song_id, song in db_songs_ids:
        if song_id == target_id:
            return song
    return None  # Return None if no matching song is found


def update_song(path):
    with open(path / "metadata.json", "r") as meta_source:
        try:
            meta = json.load(meta_source)
        except json.decoder.JSONDecodeError as e:
            print(f"\033[32mBad song at {path}: {e}\033[0m")
            return None

    lytex_path = path / "source.lytex"
    if lytex_path.exists():
        lytex_source = lytex_path.read_text()
    else:
        lytex_source = None
    verses_path = path / "verses"
    if verses_path.exists():
        verses_source = verses_path.read_text()
    else:
        verses_source = None

    with Session(engine) as session:
        song = session.exec(select(Song).where(Song.id == meta["id"])).first()
        if song:
            song, updated = update_metadata(song, meta)
            if updated:
                session.commit()
            if lytex_source and song.lytex != lytex_source:
                song.lytex = lytex_source
                session.commit()
                build_song(song, force=True)
            if verses_source and song.verses != verses_source:
                song.verses = verses_source
                session.commit()
        else:
            song = make_entry(session, meta, lytex_source, verses_source)


def process_song(meta_path, db_songs, db_songs_ids, session):
    print(f"\033[32mOpening file {meta_path}\033[0m")
    with open(meta_path, "r") as meta_source:
        try:
            meta = json.load(meta_source)
        except json.decoder.JSONDecodeError as e:
            print(f"\033[32mBad song at {meta_path}\033[0m")
            print(e)
            return None
    #    with open(meta_path.parent / "id", "r") as id_source:
    #        song_id = id_source.read()
    #        meta["id"] = song_id
    #    with open(meta_path, "w", encoding='utf8') as meta_source:
    #        meta = reformat_meta(meta)
    #        json.dump(meta, meta_source, indent=4, ensure_ascii=False)
    #    print(f"Meta: {meta}")
    lytex_path = meta_path.parent / "source.lytex"
    if lytex_path.exists():
        lytex_source = lytex_path.read_text()
    else:
        lytex_source = None

    verses_path = meta_path.parent / "verses"
    if verses_path.exists():
        verses_source = verses_path.read_text()
    else:
        verses_source = None
    song = find_song_by_id(db_songs_ids, meta["id"])

    if song is None:
        song = make_entry(session, meta, lytex_source, verses_source)
    else:
        song, updated = update_metadata(song, meta)
        if updated:
            session.commit()
        if lytex_source and song.lytex != lytex_source:
            song.lytex = lytex_source
            session.commit()
            build_song(song, force=True)
        if verses_source and song.verses != verses_source:
            song.verses = verses_source
            session.commit()


def obj_in_db(cls, cls_dict):
    with Session(engine) as session:
        objects = session.exec(select(cls)).all()
    for obj in objects:
        db_dict = obj.dict()
        del db_dict["id"]
        common_keys = set(db_dict.keys()).intersection(cls_dict.keys())
        match = all(
            cls_dict.get(key) == db_dict[key] or db_dict[key] is None
            for key in common_keys
        )
        if match:
            return obj
    return False


def add_person(person_dict):
    person = Person.from_dict(person_dict)
    with Session(engine) as session:
        session.add(person)
        session.commit()


def add_source(source_dict):
    with Session(engine) as session:
        name, surname = source_dict["author_name"].split(" ")
        person = session.exec(
            select(Person).where(Person.name == name).where(Person.surname == surname)
        ).one()
        source = Source.from_dict(source_dict, author=person)
        session.add(source)
        session.commit()


def import_library(source_path):
    if isinstance(source_path, Path):
        root = source_path
    else:
        root = Path(source_path)
    library_path = root / "library.json"

    with open(library_path, "r") as library_source:
        try:
            library = json.load(library_source)
        except json.decoder.JSONDecodeError as e:
            print("Couldn't load library.json")
            print(e)
            return 0

    for author in library["authors"]:
        if not obj_in_db(Person, author):
            add_person(author)

    for source in library["sources"]:
        if not obj_in_db(Source, source):
            add_source(source)

    fs_songs = root.glob("**/metadata.json")

    with Session(engine) as session:
        try:
            db_songs = session.exec(select(Song)).all()
            db_songs_ids = [(str(db_song.id), db_song) for db_song in db_songs]
        except Exception as e:
            print(f"Couldn't get songs from database: {e}")
        for song in fs_songs:
            process_song(song, db_songs, db_songs_ids, session)


if __name__ == "__main__":
    import_library(Path(__file__).parent / "data")
