import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import create_engine
from sqlmodel import SQLModel
from starlette.middleware.authentication import AuthenticationMiddleware

from . import config
from . import db
from . import utils
from .shortcuts import redirect
from .shortcuts import render
from .songbooks.models import Songbook
from .songs.models import Song
from .users.backend import JWTCookieBackend
from .users.decorators import login_required
from .users.models import User
from .users.schemas import UserLoginSchema
from .users.schemas import UserSignupSchema

app = FastAPI()
app.add_middleware(AuthenticationMiddleware, backend=JWTCookieBackend())
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


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    if request.user.is_authenticated:
        return render(request, "dashboard.html", {}, status_code=200)
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
    # TODO create user after email verify
    User.create_user(data["email"], data["password"].get_secret_value())
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


@app.get("/create_songbook", response_class=HTMLResponse)
def create_songbook(request: Request):
    new_id = uuid.uuid4()
    Songbook.create_songbook(new_id, request.user.username)
    return render(request, "snippets/songbook_card.html", {"id": str(uuid.uuid4())})
