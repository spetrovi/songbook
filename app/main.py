from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from starlette.middleware.authentication import AuthenticationMiddleware
from . import config
from .users.models import User
from .users.schemas import UserSignupSchema, UserLoginSchema
from . import db, utils
from .users.backend import JWTCookieBackend
from .users.decorators import login_required
from .shortcuts import render, redirect
from .songs.models import Song
from sqlmodel import select

app = FastAPI()
app.add_middleware(AuthenticationMiddleware, backend=JWTCookieBackend())
settings = config.get_settings()

from .handlers import *  # noqa


@app.on_event("startup")
def on_startup():
    # triggered when fastapi starts
    # Create all tables
    #   SQLModel.metadata.create_all(engine)
    print("startup")


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
    session_id = request.cookies.get("session_id") or None
    return render(request, "auth/login.html", {"logged_in": session_id is not None})


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


@app.get("/songs")
def song_list_view():
    with db.get_library_session() as session:
        songs = session.query(Song).all()
        statement = select(Song).where(Song.title == "Dobre ti je, Janku")
        result = session.exec(statement)
        song = result.first()
        print("First song", song)
        print("Title: ", song.source.title)
        return songs
