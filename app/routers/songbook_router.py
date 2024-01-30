from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import config
from app import db
from app.press.book import bake
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook

router = APIRouter()
settings = config.get_settings()


@router.get("/songbook_pdf/{songbook_id}", response_class=FileResponse)
def get_songbook_pdf(
    request: Request, songbook_id: str, session: Session = Depends(db.yield_session)
):
    songbook = Songbook.get_by_user_songbook_id(
        request.user.username, songbook_id, session
    )
    songs = Entry.get_songs(songbook.songbook_id, session)
    pdf_path = bake(songs, songbook, settings.templates_dir)
    return FileResponse(pdf_path)


@router.get("/songbook/{songbook_id}", response_class=HTMLResponse)
def get_songbook_detail(
    request: Request, songbook_id: str, session: Session = Depends(db.yield_session)
):
    songbook = Songbook.get_by_user_songbook_id(
        request.user.username, songbook_id, session
    )
    songs = Entry.get_songs(songbook.songbook_id, session)
    return render(
        request,
        "songbook_detail.html",
        {"songbook": songbook, "songs": songs},
    )
