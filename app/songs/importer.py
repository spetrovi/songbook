import json
from pathlib import Path

from models import Person
from models import Song
from models import Source
from sqlalchemy.exc import NoResultFound
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel

# db_file_name = str(Path(__file__).parent / "library.db")
# sqlite_url = "sqlite:///database.db"
db_file_name = str(Path(__file__).parent.parent.parent / "database.db")
sqlite_url = f"sqlite:///{db_file_name}"

engine = create_engine(sqlite_url)

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


def process_song(meta_path):
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

    with Session(engine) as session:
        try:
            statement = select(Song).where(Song.id == meta["id"])
            song = session.exec(statement).one()
            if lytex_source:
                song.lytex = lytex_source
            if verses_source:
                song.verses = verses_source
            session.commit()
        except NoResultFound:
            song = make_entry(session, meta, lytex_source, verses_source)
        except KeyError:
            song = make_entry(session, meta, lytex_source, verses_source)
            meta["id"] = str(song.id)
            with open(meta_path, "w", encoding="utf8") as meta_source:
                json.dump(meta, meta_source, indent=4, ensure_ascii=False)
    return song


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

    songs = root.glob("**/metadata.json")
    for song in songs:
        process_song(song)


if __name__ == "__main__":
    import_library(Path(__file__).parent / "data")
