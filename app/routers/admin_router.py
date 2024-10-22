import inspect as another_inspect
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy import inspect
from sqlmodel import select
from sqlmodel import Session

from app import db
from app.shortcuts import redirect
from app.shortcuts import render
from app.songbooks import models as songbooksmodels
from app.songbooks.models import Entry
from app.songbooks.models import Songbook
from app.songs import models as songsmodels
from app.songs.models import Song
from app.songs.models import SongEdit
from app.users import models as usermodels
from app.users.decorators import admin_login_required
from app.users.models import User
from app.utils import build_song

router = APIRouter(prefix="/admin")


@router.get("/", response_class=HTMLResponse)
@admin_login_required
def admin_view(request: Request, session: Session = Depends(db.yield_session)):
    classes, class_names = get_classes()
    context = {"classes": class_names}
    return render(request, "admin/admin.html", context, status_code=200)


def get_classes():
    classes_user = [
        member
        for member in another_inspect.getmembers(usermodels)
        if another_inspect.isclass(member[1])
        and member[1].__mro__[1].__name__ == "SQLModel"
    ]

    classes_songs = [
        member
        for member in another_inspect.getmembers(songsmodels)
        if another_inspect.isclass(member[1])
        and member[1].__mro__[1].__name__ == "SQLModel"
    ]

    classes_songbooks = [
        member
        for member in another_inspect.getmembers(songbooksmodels)
        if another_inspect.isclass(member[1])
        and member[1].__mro__[1].__name__ == "SQLModel"
    ]

    classes = classes_user + classes_songs + classes_songbooks
    print(classes)

    class_names = [cls[0] for cls in classes]
    return classes, class_names


@router.get("/transcript_queue", response_class=HTMLResponse)
@admin_login_required
def admin_queue(request: Request, session: Session = Depends(db.yield_session)):
    main_folder = Path("app/transcript_queue")
    images = []

    json_source = main_folder / "info.json"
    with open(json_source, "r") as f:
        info = json.load(f)

    songs = []
    for path in main_folder.rglob("*jpg"):
        images.append(path.name)

        song = session.exec(
            select(SongEdit).where(SongEdit.img_src_path == path.name)
        ).first()
        if not song:
            info["img_src_path"] = path.name
            song = SongEdit.from_dict(info)
            session.add(song)
            session.commit()
        songs.append(song)

    return render(
        request,
        "admin/transcript_queue.html",
        {"images": images, "songs": songs},
        status_code=200,
    )


@router.get("/cls/{cls_str}", response_class=HTMLResponse)
@admin_login_required
def admin_cls_view(
    request: Request, cls_str: str, session: Session = Depends(db.yield_session)
):
    classes, class_names = get_classes()
    cls = None
    for name, _cls in classes:
        if name == cls_str:
            cls = _cls
            break

    instances = session.exec(select(cls)).all()
    id_name = (inspect(cls).primary_key)[0].name

    columns = [column.name for column in inspect(cls).c]
    return render(
        request,
        "admin/objects.html",
        {
            "instances": instances,
            "columns": columns,
            "id_name": id_name,
            "classes": class_names,
        },
        status_code=200,
    )


@router.delete("/delete/{cls_str}/{_id}", response_class=HTMLResponse)
@admin_login_required
def admin_delete_object(
    request: Request,
    cls_str: str,
    _id: str,
    session: Session = Depends(db.yield_session),
):
    classes, class_names = get_classes()
    cls = None
    for name, _cls in classes:
        if name == cls_str:
            cls = _cls
            break

    id_name = (inspect(cls).primary_key)[0].name
    instance = session.exec(select(cls).where(getattr(cls, id_name) == _id)).one()
    session.delete(instance)
    session.commit()
    return HTMLResponse("", status_code=200)


@router.get("/edit/{cls_str}/{_id}", response_class=HTMLResponse)
@admin_login_required
def admin_get_object_form(
    request: Request,
    cls_str: str,
    _id: str,
    session: Session = Depends(db.yield_session),
):
    classes, class_names = get_classes()
    cls = None
    for name, _cls in classes:
        if name == cls_str:
            cls = _cls
            break

    id_name = (inspect(cls).primary_key)[0].name
    instance = session.exec(select(cls).where(getattr(cls, id_name) == _id)).one()
    columns = [column.name for column in inspect(cls).c]
    context = {
        "instance": instance,
        "columns": columns,
        "id_name": id_name,
        "classes": class_names,
    }
    return render(request, "admin/snippets/object_form.html", context, status_code=200)


# TODO careful here, we had to remove @admin_login_required because of
@router.post("/edit/{cls_str}/{_id}", response_class=HTMLResponse)
async def admin_edit_object(
    request: Request,
    cls_str: str,
    _id: str,
    session: Session = Depends(db.yield_session),
):
    user = session.exec(select(User).where(User.user_id == request.user.username)).one()
    if not user.is_admin:
        return redirect("/")
    form_data = await request.form()
    data = dict(form_data)

    classes, class_names = get_classes()
    cls = None
    for name, _cls in classes:
        if name == cls_str:
            cls = _cls
            break

    id_name = (inspect(cls).primary_key)[0].name
    instance = session.exec(select(cls).where(getattr(cls, id_name) == _id)).one()
    columns = [column.name for column in inspect(cls).c]
    for key, item in data.items():
        setattr(instance, key, item)
    session.add(instance)
    session.commit()

    context = {
        "instance": instance,
        "columns": columns,
        "id_name": id_name,
        "classes": class_names,
    }
    return render(request, "admin/snippets/object_card.html", context, status_code=200)


@router.get("/logout", response_class=HTMLResponse)
def admin_logout_get_view(
    request: Request, session: Session = Depends(db.yield_session)
):
    if not request.user.is_authenticated:
        return redirect("/login")

    classes, class_names = get_classes()
    context = {"classes": class_names}
    return render(request, "admin/logout.html", context)


@router.post("/logout", response_class=HTMLResponse)
def admin_logout_post_view(request: Request):
    return redirect("/login", remove_session=True)


# @router.get("/{object}", response_class=HTMLResponse)
# @admin_login_required
# def admin_users_view(
#    request: Request, object: str, session: Session = Depends(db.yield_session)
# ):
#    cls = None
#    if object == "users":
#        cls = User
#    if object == "songbooks":
#        cls = Songbook
#    if object == "entries":
#        cls = Entry
#
#    instances = session.query(cls).all()

#    id_name = (inspect(cls).primary_key)[0].name#

#    columns = [column.name for column in inspect(cls).c]
#    return render(
#        request,
#        "admin/objects.html",
#        {"instances": instances, "columns": columns, "id_name": id_name},
#        status_code=200,
#    )


@router.get("/regenerate/{id_name}", response_class=HTMLResponse)
@admin_login_required
def regenerate_song(
    request: Request, id_name: str, session: Session = Depends(db.yield_session)
):
    song = session.exec(select(Song).where(Song.id == id_name)).one()
    build_song(song, force=True)
    return HTMLResponse("", status_code=200)


@router.delete("/delete/{object}/{id}", response_class=HTMLResponse)
@admin_login_required
def admin_delete(
    request: Request, object: str, id: str, session: Session = Depends(db.yield_session)
):
    # TODO do some clever mapping here
    if object == "User":
        User.delete_user(id, session)
    if object == "Songbook":
        Songbook.delete_songbook(id, session)
    if object == "Entry":
        Entry.delete_entry(id, session)
    return HTMLResponse("", status_code=200)
