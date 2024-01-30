from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy import inspect
from sqlmodel import Session

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
def admin_users_view(
    request: Request, object: str, session: Session = Depends(db.yield_session)
):
    cls = None
    if object == "users":
        cls = User
    if object == "songbooks":
        cls = Songbook
    if object == "entries":
        cls = Entry

    instances = session.query(cls).all()

    id_name = (inspect(cls).primary_key)[0].name

    columns = [column.name for column in inspect(cls).c]
    return render(
        request,
        "admin/objects.html",
        {"instances": instances, "columns": columns, "id_name": id_name},
        status_code=200,
    )


@router.delete("/delete/{object}/{id}", response_class=HTMLResponse)
@admin_login_required
def admin_delete_object(
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
