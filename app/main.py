from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import select
from sqlmodel import Session
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
SQLModel.metadata.create_all(db.engine)


from .handlers import *  # noqa


@app.on_event("startup")
def on_startup():
    #    DATABASE_URL = "sqlite:///database.db"
    #    engine = create_engine(DATABASE_URL)
    #    SQLModel.metadata.create_all(engine)
    # Use Lilypond to build song fragments
    utils.build_all_songs()

    # Mount the "tmp" folder to serve files
    tmp_path = Path(__file__).parent / "tmp"
    app.mount("/tmp", StaticFiles(directory=tmp_path), name="tmp")


@login_required
def dashboard_view(request: Request, session: Session):
    context = {}
    context["songs"] = session.exec(select(Song).limit(15))
    context["sources"] = session.exec(select(Source)).all()
    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    context["songbooks"] = session.exec(statement).all()
    return render(request, "dashboard.html", context, status_code=200)


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, session: Session = Depends(db.yield_session)):
    if request.user.is_authenticated:
        user = session.exec(
            select(User).where(User.user_id == request.user.username)
        ).one()
        if user.is_admin:
            return redirect("/admin")
        return dashboard_view(request, session)
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


@app.get("/logout", response_class=HTMLResponse)
def logout_get_view(request: Request):
    if not request.user.is_authenticated:
        return redirect("/login")
    return render(request, "auth/logout.html", {})


@app.post("/logout", response_class=HTMLResponse)
def logout_post_view(request: Request):
    return redirect("/login", remove_session=True)


@app.get("/song/{song_id}", response_class=HTMLResponse)
@login_required
def get_song_detail(
    request: Request, song_id: str, session: Session = Depends(db.yield_session)
):
    statement = select(Song).where(Song.id == song_id)
    song = session.exec(statement).one()
    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    songbooks = session.exec(statement).all()

    return render(
        request,
        "song_detail.html",
        {"song": song, "songbooks": songbooks},
    )


@app.get("/source/{source_id}/{page}", response_class=HTMLResponse)
@login_required
def get_source_detail_page(
    request: Request,
    source_id: str,
    page: int = 0,
    session: Session = Depends(db.yield_session),
):
    statement = select(Source).where(Source.id == source_id)
    source = session.exec(statement).one()

    statement = (
        select(Song)
        .where(Song.source_id == source_id)
        .offset(10 * (page - 1))
        .limit(10)
    )
    songs = session.exec(statement).all()

    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    songbooks = session.exec(statement).all()
    return render(
        request,
        "snippets/songs_accordion_partial.html",
        {"source": source, "songs": songs, "songbooks": songbooks, "page": page + 1},
    )


@app.get("/source/{source_id}/", response_class=HTMLResponse)
@login_required
def get_source_detail(
    request: Request, source_id: str, session: Session = Depends(db.yield_session)
):
    statement = select(Source).where(Source.id == source_id)
    source = session.exec(statement).one()

    page = 1

    statement = (
        select(Song)
        .where(Song.source_id == source_id)
        .offset(10 * (page - 1))
        .limit(10)
    )
    songs = session.exec(statement).all()

    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    songbooks = session.exec(statement).all()
    return render(
        request,
        "source_detail.html",
        {"source": source, "songs": songs, "songbooks": songbooks, "page": page + 1},
    )
