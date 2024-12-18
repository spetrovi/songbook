import json
import subprocess
from pathlib import Path
from typing import Union

import jinja2
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from jinja2 import Environment
from sqlalchemy import func
from sqlmodel import select
from sqlmodel import Session
from typing_extensions import Annotated

from app import config
from app import db
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook
from app.songs.models import Song
from app.songs.models import SongEdit
from app.songs.models import Source
from app.users.decorators import login_required
from app.users.exceptions import UserDoesntExistException
from app.users.models import User

router = APIRouter()
settings = config.get_settings()


@router.post(
    "/add_song_to_songbook/{songbook_id}/{song_id}", response_class=HTMLResponse
)
@login_required
def add_song_to_songbook(
    request: Request,
    songbook_id: str,
    song_id: str,
    session: Session = Depends(db.yield_session),
):
    Entry.add_song(songbook_id, song_id, session)
    return HTMLResponse("", status_code=200)


@router.delete(
    "/remove_song_from_songbook/{songbook_id}/{song_id}", response_class=HTMLResponse
)
@login_required
def remove_song_from_songbook(
    request: Request,
    songbook_id: str,
    song_id: str,
    session: Session = Depends(db.yield_session),
):
    Entry.remove_song(songbook_id, song_id, session)
    return HTMLResponse("", status_code=200)


@router.post("/theme_toggle")
def theme_cookie(
    response: Response, theme: Annotated[Union[str, None], Cookie()] = None
):
    if theme == "dark":
        theme_set = "light"
    else:
        theme_set = "dark"
    response.set_cookie(key="theme", value=theme_set)
    return {}


@router.post("/songbook/sort_form", response_class=HTMLResponse)
async def post_songbook_sortform(
    request: Request, session: Session = Depends(db.yield_session)
):
    form_data = await request.form()
    songbook_id = form_data.get("songbook_id")
    item_list = list(form_data.items())
    songs = Entry.reorder_songs(item_list, songbook_id, session)
    songbook = Songbook.get_by_user_songbook_id(
        request.user.username, songbook_id, session
    )

    return render(
        request,
        "snippets/songbook_accordion.html",
        {"songs": songs, "songbook": songbook},
    )


@router.delete("/delete_songbook/{songbook_id}", response_class=HTMLResponse)
@login_required
def delete_songbook(
    request: Request, songbook_id: str, session: Session = Depends(db.yield_session)
):
    Songbook.delete_songbook(request.user.username, songbook_id, session)
    return HTMLResponse("", status_code=200)


@router.get("/create_songbook", response_class=HTMLResponse)
@login_required
def create_songbook(request: Request, session: Session = Depends(db.yield_session)):
    if not session.exec(
        select(User).where(User.user_id == request.user.username)
    ).first():
        raise UserDoesntExistException("User doesn't exists")
    songbook = Songbook.create_songbook(request.user.username, session)
    return render(
        request,
        "htmx/custom_songbook_card.html",
        {"songbook": songbook},
    )


@router.put("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
@login_required
def rename_songbook(
    request: Request,
    songbook_id: str,
    title: str = Form(...),
    description: str = Form(...),
    session: Session = Depends(db.yield_session),
):
    statement = (
        select(Songbook)
        .where(Songbook.user_id == request.user.username)
        .where(Songbook.songbook_id == songbook_id)
    )
    songbook = session.exec(statement).one()
    songbook.title = title
    songbook.description = description
    session.commit()
    session.refresh(songbook)
    return render(request, "htmx/custom_songbook_card.html", {"songbook": songbook})


@router.get("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
@login_required
def get_rename_songbook(
    request: Request, songbook_id: str, session: Session = Depends(db.yield_session)
):
    statement = (
        select(Songbook)
        #        .where(Songbook.user_id == request.user.username)
        .where(Songbook.songbook_id == songbook_id)
    )
    songbook = session.exec(statement).one()
    return render(
        request,
        "htmx/custom_songbook_edit.html",
        {"songbook": songbook},
    )


@router.get("/songbook_card_body/{songbook_id}", response_class=HTMLResponse)
@login_required
def get_songbook_card_body(request: Request, songbook_id: str):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        songbook = session.exec(statement).one()
        return render(
            request,
            "htmx/custom_songbook_card.html",
            {"songbook": songbook},
        )


@router.post("/source/filter", response_class=HTMLResponse)
async def post_source_filter(
    request: Request,
    session: Session = Depends(db.yield_session),
):
    form_data = await request.form()
    source_id = form_data.get("source_id")

    statement = select(Song).where(Song.source_id == source_id)
    for key, value in form_data.items():
        if not value:
            continue
        if key == "source_id":
            continue
        if key == "title":
            statement = statement.filter(
                func.similarity(func.unaccent(Song.title), func.unaccent(value)) > 0.5
            )
        else:
            data = json.loads(value)
            values = [item["value"] for item in data]
            song_column = getattr(Song, key, None)
            statement = statement.filter(song_column.in_(values))

    statement = (
        statement.order_by(Song.signature).order_by(Song.number).order_by(Song.page)
    )
    songs = session.exec(statement).all()

    statement = select(Source).where(Source.id == source_id)
    source = session.exec(statement).one()

    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    songbooks = session.exec(statement).all()

    return render(
        request,
        "snippets/songs_accordion_partial.html",
        {
            "source": source,
            "songs": songs,
            "songbooks": songbooks,
            "infinite_scroll": False,
        },
    )


@router.post("/song_editor/update_verses", response_class=HTMLResponse)
async def post_songbook_editor_update_verses(
    request: Request,
    session: Session = Depends(db.yield_session),
):
    # check if user has permissions to update
    # Either user must be admin or have uuid in user_id

    form_data = await request.form()
    verses = form_data.get("verses")
    songedit_id = form_data.get("songedit_id")
    song = session.exec(select(SongEdit).where(SongEdit.id == songedit_id)).one()
    song.verses = verses
    session.commit()

    return


@router.post("/song_editor/update_metadata", response_class=HTMLResponse)
async def post_songbook_editor_update_metadata(
    request: Request,
    session: Session = Depends(db.yield_session),
):
    form_data = await request.form()
    songedit_id = form_data.get("songedit_id")
    song = session.exec(select(SongEdit).where(SongEdit.id == songedit_id)).one()

    metadata = {
        "title": form_data.get("title"),
        "signature": form_data.get("signature"),
        "page": form_data.get("page"),
        "number": form_data.get("number"),
        "type": form_data.get("type"),
        "year": form_data.get("year"),
        "location": form_data.get("location"),
        "recorded_by_name": form_data.get("recorded_by_name"),
        "recorded_by_surname": form_data.get("recorded_by_surname"),
        "recorded_name": form_data.get("recorded_name"),
        "recorded_surname": form_data.get("recorded_surname"),
        "recorded_age": form_data.get("recorded_age"),
    }
    song.update_from_dict(metadata)
    session.commit()
    return


@router.post("/song_editor/update_lytex", response_class=HTMLResponse)
async def post_songbook_editor_update_lytex(
    request: Request,
    session: Session = Depends(db.yield_session),
):
    # check if user has permissions to update
    # Either user must be admin or have uuid in user_id
    form_data = await request.form()
    autobeamoff = True if form_data.get("autobeamoff") == "on" else False

    print(autobeamoff)
    time_numerator = form_data.get("time_numerator")
    time_denominator = form_data.get("time_denominator")
    key_value = form_data.get("key_value")
    key_type = form_data.get("key_type")
    tempo = None if not form_data.get("tempo") else form_data.get("tempo")
    tempomidi = form_data.get("tempomidi")
    firsttone = form_data.get("firsttone")
    tones = form_data.get("tones")
    uuid = form_data.get("uuid")
    instrument = form_data.get("instrument")

    song = session.exec(select(SongEdit).where(SongEdit.id == uuid)).one()

    # Creating a dictionary to pass to the template
    template_data = {
        "autobeamoff": autobeamoff,
        "time_numerator": time_numerator,
        "time_denominator": time_denominator,
        "key_value": key_value,
        "key_type": key_type,
        "tempo": tempo,
        "tempomidi": tempomidi,
        "firsttone": firsttone,
        "tones": tones,
        "instrument": instrument,
    }

    song.update_from_dict(template_data)
    session.commit()

    env = Environment(
        loader=jinja2.FileSystemLoader(settings.templates_dir),
    )

    song_template = env.get_template("song.jinja2")
    song_lytex = song_template.render(template_data)

    dest_path = Path("app/tmp/editor/" + uuid)
    dest_path.mkdir(parents=True, exist_ok=True)
    source = dest_path / "source.lytex"

    with source.open(mode="w") as file:
        source_lytex = "#(ly:set-option 'crop #t)\n" + song_lytex
        file.write(source_lytex)

    subprocess.run(["lilypond", "-o", dest_path.resolve(), source.resolve()])

    return
