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

# import abjad


db_file_name = str(Path(__file__).parent / "library.db")
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


def process_song(meta_path, source_list, person_list):
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
        statement = select(Song).where(Song.id == meta["id"])
        try:
            song = session.exec(statement).one()
        except NoResultFound:
            source = find_source_by_title(source_list, meta["source"]["title"])
            if meta["recorded_by"]:
                recorded_by = find_person_by_name(person_list, meta["recorded_by"])
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
            print(song.location)

    return song


def find_person_by_name(person_list, author_name):
    for person in person_list:
        if person.name in author_name and person.surname in author_name:
            return person
    return None


def find_person_by_dict(person_list, person_dict):
    if not person_dict:
        return None
    for person in person_list:
        if (
            person.name in person_dict["name"]
            and person.surname in person_dict["surname"]
            and person.born == person_dict["born"]
        ):
            return person
    return Person.from_dict(person_dict)


def find_source_by_title(source_list, title):
    for source in source_list:
        if title == source.title:
            return source
    return None


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

    person_list = [Person.from_dict(author) for author in library["authors"]]
    source_list = []
    for source in library["sources"]:
        person_obj = find_person_by_name(person_list, source["author_name"])
        source_list.append(Source.from_dict(source, author=person_obj))
    meta_paths = root.glob("**/metadata.json")
    song_list = []
    for meta_path in meta_paths:
        song_list.append(process_song(meta_path, source_list, person_list))

    with Session(engine) as session:
        for person in person_list:
            session.add(person)

        for source in source_list:
            session.add(source)

        for song in song_list:
            session.add(song)

        session.commit()


if __name__ == "__main__":
    import_library(Path(__file__).parent / "data")
