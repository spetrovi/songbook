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
from .routers.htmx_router import router as htmx_router
from .routers.songbook_router import router as songbook_router
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
app.include_router(htmx_router)
app.include_router(songbook_router)
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
        context["songs"] = session.exec(select(Song).limit(15))
        context["sources"] = session.query(Source).all()
        with db.get_session() as session:
            statement = select(Songbook).where(
                Songbook.user_id == request.user.username
            )
            result = session.exec(statement)
            songbooks_all = result.all()
            songbooks = [songbook.dict() for songbook in songbooks_all]
            for songbook in songbooks:
                songbook["song_count"] = Entry.count_songs(songbook["songbook_id"])
            context["songbooks"] = songbooks
            return render(request, "dashboard.html", context, status_code=200)


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    if request.user.is_authenticated:
        return dashboard_view(request)
    return redirect("/login")


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
    context = {"register_enabled": settings.register_enabled}
    return render(request, "auth/signup.html", context)


@app.post("/signup", response_class=HTMLResponse)
def signup_post_view(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    if not settings.register_enabled:
        return redirect("/login")
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


@login_required
@app.get("/song/{song_id}", response_class=HTMLResponse)
def get_song_detail(request: Request, song_id: str):
    with db.get_library_session() as lib_session:
        statement = select(Song).where(Song.id == song_id)
        song = lib_session.exec(statement).one()
        with db.get_session() as session:
            statement = select(Songbook).where(
                Songbook.user_id == request.user.username
            )
            songbooks = session.exec(statement).all()

            return render(
                request,
                "song_detail.html",
                {"song": song, "songbooks": songbooks},
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

        with db.get_session() as user_session:
            statement = select(Songbook).where(
                Songbook.user_id == request.user.username
            )
            songbooks = user_session.exec(statement).all()
            return render(
                request,
                "source_detail.html",
                {"source": source, "songs": songs, "songbooks": songbooks},
            )
