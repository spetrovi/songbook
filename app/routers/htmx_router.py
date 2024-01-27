from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from app import db
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook
from app.users.decorators import login_required

router = APIRouter()


@login_required
@router.post(
    "/add_song_to_songbook/{songbook_id}/{song_id}", response_class=HTMLResponse
)
def add_song_to_songbook(request: Request, songbook_id: str, song_id: str):
    Entry.add_song(songbook_id, song_id)
    return HTMLResponse("", status_code=200)


@login_required
@router.delete(
    "/remove_song_from_songbook/{songbook_id}/{song_id}", response_class=HTMLResponse
)
def remove_song_from_songbook(request: Request, songbook_id: str, song_id: str):
    Entry.remove_song(songbook_id, song_id)
    return HTMLResponse("", status_code=200)


@router.post("/songbook/sort_form", response_class=HTMLResponse)
async def post_songbook_sortform(request: Request):
    form_data = await request.form()
    songbook_id = form_data.get("songbook_id")
    item_list = list(form_data.items())
    print(item_list)
    songbook = Songbook.get_by_user_songbook_id(request.user.username, songbook_id)
    sorted_entry_ids = Entry.reorder_songs(item_list)
    songs = [Entry.get_song_by_entry_id(entry_id) for entry_id in sorted_entry_ids]

    return render(
        request,
        "snippets/songbook_accordion.html",
        {"songs": songs, "songbook": songbook},
    )


# TODO Rewrite this so we don't hit database two times
# Either pass user id to the delete_songbook or don't use it
@login_required
@router.delete("/delete_songbook/{songbook_id}", response_class=HTMLResponse)
def delete_songbook(request: Request, songbook_id: str):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        songbook = session.exec(statement).one()

        Songbook.delete_songbook(songbook.songbook_id)

        return HTMLResponse("", status_code=200)


@login_required
@router.get("/create_songbook", response_class=HTMLResponse)
def create_songbook(request: Request):
    songbook = Songbook.create_songbook(request.user.username)
    return render(
        request,
        "snippets/new_songbook_slide.html",
        {"songbook": songbook},
    )


@login_required
@router.put("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
def rename_songbook(request: Request, songbook_id: str, title: str = Form(...)):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        songbook = session.exec(statement).one()
        songbook.title = title
        session.commit()
        return render(request, "snippets/songbook_body.html", {"songbook": songbook})


@router.get("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
def get_rename_songbook(request: Request, songbook_id: str):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        songbook = session.exec(statement).one()
        return render(
            request,
            "snippets/rename_songbook_form.html",
            {"title": songbook.title, "songbook_id": songbook.songbook_id},
        )


@login_required
@router.get("/songbook_card_body/{songbook_id}", response_class=HTMLResponse)
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
            "snippets/songbook_body.html",
            {"songbook": songbook},
        )
