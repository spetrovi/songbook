from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from app import db
from app.shortcuts import render
from app.songbooks.models import Entry
from app.songbooks.models import Songbook
from app.users.decorators import admin_login_required
from app.users.models import User

router = APIRouter(prefix="/admin")


@router.get("/", response_class=HTMLResponse)
@admin_login_required
def admin_view(request: Request):
    context = {}
    return render(request, "admin/admin.html", context, status_code=200)


@router.get("/{object}", response_class=HTMLResponse)
@admin_login_required
def admin_users_view(request: Request, object: str):
    cls = None
    # TODO do some clever mapping here
    if object == "users":
        cls = User
        id_name = "user_id"
        display_fields = ["email", "is_admin"]
    if object == "songbooks":
        cls = Songbook
        id_name = "songbook_id"
        display_fields = ["user_id", "songbook_id"]
    if object == "entries":
        cls = Entry
        id_name = "id"
        display_fields = ["songbook_id", "song_id", "order"]

    with db.get_session() as session:
        objects = session.exec(select(cls)).all()
        context_objects = [item.dict() for item in objects]
        for item in context_objects:
            item["id"] = item[id_name]
            item["cls_name"] = cls.__name__
            item["display_fields"] = display_fields
    return render(
        request,
        "admin/objects.html",
        {"context_objects": context_objects},
        status_code=200,
    )


@router.delete("/delete/{object}/{id}", response_class=HTMLResponse)
@admin_login_required
def admin_delete_object(request: Request, object: str, id: str):
    # TODO do some clever mapping here
    if object == "User":
        User.delete_user(id)
    if object == "Songbook":
        Songbook.delete_songbook(id)
    if object == "Entry":
        Entry.delete_entry(id)
    return HTMLResponse("", status_code=200)
