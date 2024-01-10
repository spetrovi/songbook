import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import SQLModel
from starlette.middleware.authentication import AuthenticationMiddleware

from . import config
from . import db
from . import utils
from .routers.admin_router import router as admin_router
from .shortcuts import redirect
from .shortcuts import render
from .songbooks.models import Entry
from .songbooks.models import Songbook
from .songs.models import Song
from .songs.models import Source
from .users.backend import JWTCookieBackend
from .users.decorators import login_required
from .users.models import User
from .users.schemas import UserLoginSchema
from .users.schemas import UserSignupSchema

app = FastAPI()
app.add_middleware(AuthenticationMiddleware, backend=JWTCookieBackend())
app.include_router(admin_router)
settings = config.get_settings()

from .handlers import *  # noqa


@app.on_event("startup")
def on_startup():
    DATABASE_URL = "sqlite:///database.db"
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    # Use Lilypond to build song fragments
    utils.build_all_songs()

    # Mount the "tmp" folder to serve files
    tmp_path = Path(__file__).parent / "tmp"
    app.mount("/tmp", StaticFiles(directory=tmp_path), name="tmp")


@login_required
def dashboard_view(request: Request):
    # we need to get user's songbooks, all books and all songs
    context = {}
    with db.get_library_session() as session:
        songs_all = session.query(Song).all()
        songs = [song.dict() for song in songs_all]
        context["songs"] = songs

        sources_all = session.query(Source).all()
        sources = [source.dict() for source in sources_all]
        context["sources"] = sources

    with db.get_session() as session:
        statement = select(Songbook).where(Songbook.user_id == request.user.username)
        result = session.exec(statement)
        songbooks_all = result.all()
        songbooks = [songbook.dict() for songbook in songbooks_all]
        context["songbooks"] = songbooks

    return render(request, "dashboard.html", context, status_code=200)


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    if request.user.is_authenticated:
        return dashboard_view(request)
    context = {}
    return render(request, "home.html", context)


@app.get("/account", response_class=HTMLResponse)
@login_required
def account_view(request: Request):
    context = {}
    return render(request, "account.html", context)


@app.get("/login", response_class=HTMLResponse)
def login_get_view(request: Request):
    return render(request, "auth/login.html", {})


@app.post("/login", response_class=HTMLResponse)
def login_post_view(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    raw_data = {
        "email": email,
        "password": password,
    }
    data, errors = utils.valid_schema_data_or_error(raw_data, UserLoginSchema)
    context = {"data": data, "errors": errors}
    if len(errors) > 0:
        return render(request, "auth/login.html", context, status_code=400)
    return redirect("/", cookies=data)


@app.get("/signup", response_class=HTMLResponse)
def signup_get_view(request: Request):
    context = {}
    return render(request, "auth/signup.html", context)


@app.post("/signup", response_class=HTMLResponse)
def signup_post_view(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    raw_data = {
        "email": email,
        "password": password,
        "password_confirm": password_confirm,
    }
    data, errors = utils.valid_schema_data_or_error(raw_data, UserSignupSchema)
    context = {"data": data, "errors": errors}
    if len(errors) > 0:
        return render(request, "auth/signup.html", context, status_code=400)
    try:
        User.create_user(data["email"], data["password"].get_secret_value())
    except Exception as e:
        errors.append({"msg": e})
    context = {"data": data, "errors": errors}
    if len(errors) > 0:
        return render(request, "auth/signup.html", context, status_code=400)
    return redirect("/login")


@app.get("/users")
def users_list_view():
    with db.get_session() as session:
        users = session.query(User).all()
        return users


@app.get("/get_songs")
def get_songs():
    with db.get_library_session() as session:
        songs_all = session.query(Song).all()
        songs = [song.dict() for song in songs_all]
        return {"songs": songs}


# Get songs from the database
@app.get("/songs", response_class=HTMLResponse)
def songs_view(request: Request):
    return render(request, "songs.html", context=get_songs())


@app.delete("/delete_songbook/{songbook_id}", response_class=HTMLResponse)
def delete_songbook(request: Request, songbook_id: str):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        result = session.exec(statement)
        songbook = result.one()

        Songbook.delete_songbook(songbook.songbook_id)

        return HTMLResponse("", status_code=200)


@app.get("/create_songbook", response_class=HTMLResponse)
def create_songbook(request: Request):
    new_id = uuid.uuid4()
    Songbook.create_songbook(new_id, request.user.username)
    songbook = {"title": "Untitled", "songbook_id": str(new_id)}
    return render(
        request,
        "snippets/new_songbook_slide.html",
        {"songbook": songbook},
    )


@app.put("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
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


@app.get("/rename_songbook/{songbook_id}", response_class=HTMLResponse)
def get_rename_songbook(request: Request, songbook_id: str):
    with db.get_session() as session:
        statement = (
            select(Songbook)
            .where(Songbook.user_id == request.user.username)
            .where(Songbook.songbook_id == songbook_id)
        )
        result = session.exec(statement)
        songbook = result.first()
        return render(
            request,
            "snippets/rename_songbook_form.html",
            {"title": songbook.title, "songbook_id": songbook.songbook_id},
        )


@app.get("/songbook_card_body/{songbook_id}", response_class=HTMLResponse)
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


@app.get("/song/{song_id}", response_class=HTMLResponse)
def get_song_detail(request: Request, song_id: str):
    with db.get_library_session() as session:
        statement = select(Song).where(Song.id == song_id)
        result = session.exec(statement)
        song = result.first()

    with db.get_session() as session:
        statement = select(Songbook).where(Songbook.user_id == request.user.username)
        result = session.exec(statement)
        songbooks = result.all()

    return render(
        request,
        "song_detail.html",
        {"song": song, "songbooks": songbooks},
    )


@app.post("/songbook/sort_form", response_class=HTMLResponse)
async def post_songbook_sortform(request: Request):
    form_data = await request.form()
    songbook_id = form_data.get("songbook_id")
    item_list = list(form_data.items())
    songbook = Songbook.get_by_user_songbook_id(request.user.username, songbook_id)
    sorted_entry_ids = Entry.reorder_songs(item_list)
    songs = [Entry.get_song_by_entry_id(entry_id) for entry_id in sorted_entry_ids]

    return render(
        request,
        "snippets/songbook_accordion.html",
        {"songs": songs, "songbook": songbook},
    )


@app.get("/source/{source_id}", response_class=HTMLResponse)
def get_source_detail(request: Request, source_id: str):
    with db.get_library_session() as session:
        statement = select(Source).where(Source.id == source_id)
        result = session.exec(statement)
        source = result.first()

        statement = select(Song).where(Song.source_id == source_id)
        result = session.exec(statement)
        songs = result.all()

        return render(
            request,
            "source_detail.html",
            {"source": source, "songs": songs},
        )


@app.get("/songbook/{songbook_id}", response_class=HTMLResponse)
def get_ssongbook_detail(request: Request, songbook_id: str):
    songbook = Songbook.get_by_user_songbook_id(request.user.username, songbook_id)
    songs = Entry.get_songs(songbook.songbook_id)
    return render(
        request,
        "songbook_detail.html",
        {"songbook": songbook, "songs": songs},
    )


@app.post("/add_song_to_songbook/{songbook_id}/{song_id}", response_class=HTMLResponse)
def add_song_to_songbook(request: Request, songbook_id: str, song_id: str):
    Entry.add_song(songbook_id, song_id)
    return HTMLResponse("", status_code=200)
