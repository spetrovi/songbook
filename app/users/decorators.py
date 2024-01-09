from functools import wraps

from fastapi import Request
from sqlalchemy.exc import NoResultFound
from sqlmodel import select

from .exceptions import AdminRequiredException
from .exceptions import LoginRequiredException
from .models import User
from app.db import get_session


def login_required(func):
    @wraps(func)
    def wrapper(request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise LoginRequiredException(status_code=401)
        return func(request, *args, **kwargs)

    return wrapper


def admin_login_required(func):
    @wraps(func)
    def wrapper(request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise LoginRequiredException(status_code=401)
        with get_session() as session:
            statement = (
                select(User)
                .where(User.user_id == request.user.username)
                .where(User.is_admin)
            )
            try:
                session.exec(statement).one()
            except NoResultFound:
                raise AdminRequiredException(status_code=401)
        return func(request, *args, **kwargs)

    return wrapper
