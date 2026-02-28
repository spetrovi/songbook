from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel
from starlette.middleware.authentication import AuthenticationMiddleware
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import config
from . import db
from . import utils
from .routers.admin_router import router as admin_router
from .routers.htmx_router import router as htmx_router
from .routers.songbook_router import router as songbook_router
from .shortcuts import redirect
from .shortcuts import render
from .songbooks.models import Songbook
from .songs.importer import update_song  # noqa
from .songs.models import Song
from .songs.models import SongEdit
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
    # Mount the "tmp" folder to serve files
    tmp_path = Path(__file__).parent / "tmp"
    app.mount("/tmp", StaticFiles(directory=tmp_path), name="tmp")

    # Mount the "tmp" folder to serve files
    queue_path = Path(__file__).parent / "transcript_queue"
    app.mount(
        "/transcript_queue", StaticFiles(directory=queue_path), name="transcript_queue"
    )

    # Mount the "tmp" folder to serve files
    queue_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=queue_path), name="static")


class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory and all(
            not part.startswith(".") for part in Path(event.src_path).parts
        ):
            try:
                update_song(Path(event.src_path))
            except Exception as e:
                print(f"Couldn't update song on {event.src_path}: {e}")


@app.on_event("startup")
def start_file_watcher():
    observer = Observer()
    observer.schedule(FileChangeHandler(), "app/songs/data", recursive=True)
    observer.start()


@login_required
def dashboard_view(request: Request, session: Session):
    context = {}
    context["sources"] = session.exec(select(Source)).all()
    # OPTIMISE THIS PLEASE
    context["songs_per_source"] = {}
    for source in context["sources"]:
        context["songs_per_source"][source.title] = str(
            len(session.exec(select(Song).where(Song.source_id == source.id)).all())
        )
    statement = select(Songbook).where(Songbook.user_id == request.user.username)
    context["songbooks"] = session.exec(statement).all()
    return render(request, "dashboard.html", context, status_code=200)


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, session: Session = Depends(db.yield_session)):
    if request.user.is_authenticated:
        user = session.exec(
            select(User).where(User.user_id == request.user.username)
        ).first()
        if not user:
            return redirect("/login")
        if user.is_admin:
            return redirect("/admin")
        return dashboard_view(request, session)
    return landing_view(request, session)


@app.get("/landing", response_class=HTMLResponse)
def landing_view(request: Request, session):
    context = {}
    context["sources"] = session.exec(
        select(Source).where(Source.public.is_(True))
    ).all()

    # One query to get counts of songs per source
    results = session.exec(
        select(Song.source_id, func.count(Song.id)).group_by(Song.source_id)
    ).all()

    # Turn into a dictionary keyed by source_id
    songs_per_source = {source_id: count for source_id, count in results}

    # Map source titles to counts (default to 0 if no songs)
    context["songs_per_source"] = {
        source.title: str(songs_per_source.get(source.id, 0))
        for source in context["sources"]
    }
    return render(request, "landing.html", context)


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
    return redirect("/", remove_session=True)


@app.get("/song/{song_id}", response_class=HTMLResponse)
def get_song_detail(
    request: Request, song_id: str, session: Session = Depends(db.yield_session)
):
    statement = select(Song).where(Song.id == song_id)
    song = session.exec(statement).one()
    if request.user.is_authenticated:
        statement = select(Songbook).where(Songbook.user_id == request.user.username)
        songbooks = session.exec(statement).all()
    else:
        songbooks = []
    return render(
        request,
        "song_detail.html",
        {"song": song, "songbooks": songbooks},
    )


@app.get("/source/{source_id}/{page}", response_class=HTMLResponse)
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
        .order_by(Song.signature)
        .order_by(Song.page)
        .order_by(Song.number)
        .offset(10 * (page - 1))
        .limit(10)
    )
    songs = session.exec(statement).all()

    if request.user.is_authenticated:
        statement = select(Songbook).where(Songbook.user_id == request.user.username)
        songbooks = session.exec(statement).all()
    else:
        songbooks = []
    return render(
        request,
        "snippets/songs_accordion_partial.html",
        {
            "source": source,
            "songs": songs,
            "songbooks": songbooks,
            "page": page + 1,
            "infinite_scroll": True,
        },
    )


def generate_filters(source, session) -> [dict]:
    filter_names = ["location", "title"]
    if source.type == "archive":
        filter_names.append("signature")

    hinted = ["location", "signature"]

    filter_list = []

    for filter_name in filter_names:
        filter_dict = {"type": filter_name, "hinted": False, "hints": None}
        if filter_name in hinted:
            song_column = getattr(Song, filter_name, None)
            filter_dict["hinted"] = True
            filter_dict["hints"] = session.exec(
                select(song_column).where(Song.source_id == source.id).distinct()
            ).all()
        #            print(filter_dict["hints"])
        filter_list.append(filter_dict)
    return filter_list


@app.get("/source/{source_id}/", response_class=HTMLResponse)
def get_source_detail(
    request: Request, source_id: str, session: Session = Depends(db.yield_session)
):
    source = session.exec(select(Source).where(Source.id == source_id)).one()
    page = 1
    statement = (
        select(Song)
        .where(Song.source_id == source_id)
        .order_by(Song.signature)
        .order_by(Song.page)
        .order_by(Song.number)
        .offset(10 * (page - 1))
        .limit(10)
    )
    songs = session.exec(statement).all()

    filters = generate_filters(source, session)

    if request.user.is_authenticated:
        statement = select(Songbook).where(Songbook.user_id == request.user.username)
        songbooks = session.exec(statement).all()
    else:
        songbooks = []
    return render(
        request,
        "source_detail.html",
        {
            "source": source,
            "songs": songs,
            "songbooks": songbooks,
            "page": page + 1,
            "infinite_scroll": True,
            "filters": filters,
        },
    )


@app.get("/song_editor/{songedit_id}", response_class=HTMLResponse)
@login_required
def get_song_editor(
    request: Request, songedit_id: str, session: Session = Depends(db.yield_session)
):
    # check if user can edit this song

    song = session.exec(select(SongEdit).where(SongEdit.id == songedit_id)).one()

    metadata = {
        "title": song.title,
        "signature": song.signature,
        "page": song.page,
        "number": song.number,
        "type": song.type,
        "year": song.year,
        "location": song.location,
        "recorded_by_name": song.recorded_by_name,
        "recorded_by_surname": song.recorded_by_surname,
        "recorded_name": song.recorded_name,
        "recorded_surname": song.recorded_surname,
        "recorded_age": song.recorded_age,
    }
    return render(
        request,
        "song_editor.html",
        {"song": song, "metadata": metadata, "rows": 20, "songedit_id": songedit_id},
    )


@app.get("/transcript_queue", response_class=HTMLResponse)
@login_required
def transcript_queue(request: Request, session: Session = Depends(db.yield_session)):
    # give me songedits
    songs = session.exec(
        select(SongEdit)
        .where(SongEdit.user_id == request.user.username)
        .order_by(SongEdit.img_src_path)
    ).all()
    # Extract unique folders
    unique_folders = {str(Path(song.img_src_path).parent) for song in songs}
    folders = list(unique_folders)

    return render(
        request,
        "transcript_queue.html",
        {"songs": songs, "folders": folders},
        status_code=200,
    )
