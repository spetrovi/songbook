from typing import Union

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from sqlmodel import select
from sqlmodel import Session
from typing_extensions import Annotated

from app import db
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook
from app.users.decorators import login_required
from app.users.exceptions import UserDoesntExistException
from app.users.models import User

router = APIRouter()


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
        "htmx/songbook_slide.html",
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
    return render(request, "htmx/songbook_slide.html", {"songbook": songbook})


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
        "htmx/songbook_slide_form.html",
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
            "htmx/songbook_slide.html",
            {"songbook": songbook},
        )
