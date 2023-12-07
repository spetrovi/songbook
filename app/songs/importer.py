import json
from models import Person, Source, Song
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine


def process_song(meta_path, source_list):
    with open(meta_path, "r") as meta_source:
        try:
            meta = json.load(meta_source)
        except json.decoder.JSONDecodeError as e:
            print(f"\033[32mBad song at {meta_path}\033[0m")
            print(e)
            return None

    source = find_source_by_title(source_list, meta["source"]["title"])
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
    return Song(
        title=meta["title"], source=source, lytex=lytex_source, verses=verses_source
    )


def find_person_by_name(person_list, author_name):
    for person in person_list:
        if person.name in author_name and person.surname in author_name:
            return person
    return None


def find_source_by_title(source_list, title):
    for source in source_list:
        if title in source.title:
            return source
    return None


def import_library(source_path):
    if isinstance(source_path, Path):
        root = source_path
    else:
        root = Path(source_path)
    library_path = root / "library.json"

    with open(library_path, "r") as library_source:
        library = json.load(library_source)

    person_list = [Person.from_dict(author) for author in library["authors"]]
    source_list = []
    for source in library["sources"]:
        person_obj = find_person_by_name(person_list, source["author_name"])
        source_list.append(Source.from_dict(source, author=person_obj))

    meta_paths = root.glob("**/metadata.json")
    song_list = list(
        filter(None, [process_song(meta_path, source_list) for meta_path in meta_paths])
    )

    db_file_name = "library.db"
    sqlite_url = f"sqlite:///{db_file_name}"

    engine = create_engine(sqlite_url, echo=True)

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for person in person_list:
            session.add(person)

        for source in source_list:
            session.add(source)

        for song in song_list:
            session.add(song)

        session.commit()


if __name__ == "__main__":
    import_library("./data")
