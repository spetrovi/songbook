from fastapi import HTTPException


class LoginRequiredException(HTTPException):
    pass
