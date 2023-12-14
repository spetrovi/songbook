import json
import subprocess
from pathlib import Path

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from . import db
from .songs.models import Song


def valid_schema_data_or_error(raw_data: dict, SchemaModel: BaseModel):
    data = {}
    errors = []
    error_str = None
    try:
        cleaned_data = SchemaModel(**raw_data)
        data = cleaned_data.dict()
    except ValidationError as e:
        error_str = e.json()
    if error_str is not None:
        try:
            errors = json.loads(error_str)
        except Exception:
            errors = [{"loc": "non_field_error", "msg": "Unknown error"}]
    return data, errors


def build_song(song):
    dest_path = Path("app/tmp/" + str(song.id))
    pdf_path = dest_path / "source.pdf"
    if pdf_path.exists():
        return
    dest_path.mkdir(parents=True, exist_ok=True)
    source = dest_path / "source.lytex"

    with source.open(mode="w") as file:
        source_lytex = "#(ly:set-option 'crop #t)\n" + song.lytex
        file.write(source_lytex)

    subprocess.run(["lilypond", "-o", dest_path, source])
    return


def build_all_songs():
    with db.get_library_session() as session:
        songs = session.query(Song).all()
        for song in songs:
            build_song(song)
