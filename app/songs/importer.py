import json
import subprocess
import tempfile
from pathlib import Path

from models import Person
from models import Song
from models import Source
from sqlmodel import create_engine
from sqlmodel import Session
from sqlmodel import SQLModel

# import abjad


def create_pdf(lytex_source):
    # if you wonder why we do it like this,
    # it's because lilypond dies when encountering whitespace
    # in file path
    # Also, we don't get logs to clutter our filesystem
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source = temp_path / "source.lytex"
        pdf_path = temp_path / "source.pdf"
        with source.open(mode="w") as file:
            file.write(lytex_source)
        subprocess.run(["lilypond", "-o", temp_path, source])
        return pdf_path.read_bytes()


def process_song(meta_path, source_list):
    print(f"\033[32mOpening file {meta_path}\033[0m")
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
    #        pdf_content = create_pdf(lytex_source)
    else:
        lytex_source = None

    verses_path = meta_path.parent / "verses"
    if verses_path.exists():
        verses_source = verses_path.read_text()
    else:
        verses_source = None
    return Song(
        title=meta["title"],
        source=source,
        lytex=lytex_source,
        verses=verses_source,
        #        pdf_partial=pdf_content,
    )


def find_person_by_name(person_list, author_name):
    for person in person_list:
        if person.name in author_name and person.surname in author_name:
            return person
    return None


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
    song_list = list(
        filter(None, [process_song(meta_path, source_list) for meta_path in meta_paths])
    )

    db_file_name = str(Path(__file__).parent / "library.db")
    sqlite_url = f"sqlite:///{db_file_name}"

    engine = create_engine(sqlite_url)

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
    import_library(Path(__file__).parent / "data")
