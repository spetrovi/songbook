from starlette.authentication import AuthCredentials
from starlette.authentication import AuthenticationBackend
from starlette.authentication import SimpleUser
from starlette.authentication import UnauthenticatedUser

from . import auth


class JWTCookieBackend(AuthenticationBackend):
    async def authenticate(self, request):
        session_id = request.cookies.get("session_id")
        user_data = auth.verify_session_id(session_id)
        if user_data is None:
            roles = ["anon"]
            return AuthCredentials(roles), UnauthenticatedUser()
        user_id = user_data.get("user_id")
        roles = ["authenticated"]
        return AuthCredentials(), SimpleUser(user_id)  # request
