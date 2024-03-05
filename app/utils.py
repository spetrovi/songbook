import json
import subprocess
from pathlib import Path

from PIL import Image
from PIL import ImageOps
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
            errors = [{"msg": "Unknown error"}]
    return data, errors


def dark_theme_png(dest_path):
    # Open the inverted PNG image
    image = Image.open(dest_path / "source.cropped.png")

    image = ImageOps.invert(image)

    # Define the target colors (dark gray and slightly darker gray)
    dark_gray_color = (33, 37, 41)  # RGB values for #212529
    darker_white_color = (200, 200, 200)  # Adjusted slightly darker shade of white

    # Get the image dimensions
    width, height = image.size

    # Loop through each pixel in the image
    for x in range(width):
        for y in range(height):
            pixel_color = image.getpixel((x, y))

            # If the pixel color is black, replace it with the dark gray color
            if pixel_color == (0, 0, 0):
                image.putpixel((x, y), dark_gray_color)
            # If the pixel color is white, replace it with the slightly darker white color
            elif pixel_color == (255, 255, 255):
                image.putpixel((x, y), darker_white_color)

    # Save the modified image
    image.save(dest_path / "source.cropped.dark.png")


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

    subprocess.run(["lilypond", "-o", dest_path.resolve(), source.resolve()])

    dark_theme_png(dest_path)
    return


def build_all_songs():
    with db.get_session() as session:
        songs = session.query(Song).all()
        for song in songs:
            if song.lytex:
                build_song(song)
