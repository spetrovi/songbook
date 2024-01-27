from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse

from app import config
from app.press.book import bake
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook

router = APIRouter()
settings = config.get_settings()


@router.get("/songbook_pdf/{songbook_id}", response_class=FileResponse)
def get_songbook_pdf(request: Request, songbook_id: str):
    # TODO This is not good, because we won't generate new pdf if
    # user rearanges songs
    #    pdf_path = Path("app/tmp/songbooks/") / songbook_id / "output/songbook.pdf"
    #    if pdf_path.exists():
    #        return FileResponse(pdf_path)
    songbook = Songbook.get_by_user_songbook_id(request.user.username, songbook_id)
    songs = Entry.get_songs(songbook.songbook_id)
    pdf_path = bake(songs, songbook, settings.templates_dir)
    return FileResponse(pdf_path)


@router.get("/songbook/{songbook_id}", response_class=HTMLResponse)
def get_songbook_detail(request: Request, songbook_id: str):
    songbook = Songbook.get_by_user_songbook_id(request.user.username, songbook_id)
    songs = Entry.get_songs(songbook.songbook_id)
    return render(
        request,
        "songbook_detail.html",
        {"songbook": songbook, "songs": songs},
    )
