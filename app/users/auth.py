import datetime

from jose import ExpiredSignatureError
from jose import jwt

from .models import User
from app import config
from app.db import get_session

settings = config.get_settings()


def authenticate(email, password):
    # step 1
    try:
        with get_session():
            user_obj = User.get_by_email(email)
    except Exception:  # TODO catch other exceptions
        user_obj = None
    if not user_obj or not user_obj.verify_password(password):
        return None
    return user_obj


def login(user_obj, expires=settings.session_duration):
    # step 2
    raw_data = {
        "user_id": f"{user_obj.user_id}",
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires),
    }
    return jwt.encode(raw_data, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_session_id(token):
    # step 3
    data = {}
    try:
        data = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except ExpiredSignatureError as e:
        print(e, "log out user")
    except Exception:
        pass
    if "user_id" not in data:
        return None
    # if 'user_id' not in data.keys():
    #     return None
    return data
