from typing import Sequence, Tuple, Union

from starlette.requests import HTTPConnection
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
    UnauthenticatedUser,
)

from api.v1.auth.schemas.errors import (
    CustomUnauthorizedError,
    CustomDecodeTokenError,
    CustomInvalidTokenError,
    CustomExpiredTokenError,
)
from api.v1.auth.schemas.exceptions import DecodeTokenException, ExpiredTokenException
from api.v1.auth.service import AuthService
from api.v1.user.schemas.responses import SystemUser


class AuthBackend(AuthenticationBackend):
    def __init__(
            self, prefix: str,
            exclude_paths: Sequence[str],
            auth_service: AuthService = AuthService()
    ):
        self.prefix = prefix
        self.exclude_paths = exclude_paths if exclude_paths else []
        self.auth_service = auth_service

async def authenticate(self, conn: HTTPConnection) -> Tuple[bool, Union[SystemUser, UnauthenticatedUser]]:
    current_path = self._get_current_path(conn)

    if self._is_excluded_path(current_path):
        return False, UnauthenticatedUser()

    token = self._get_token_from_headers(conn)
    user = await self._get_user_from_token(token, conn)

    return True, user


def _get_current_path(self, conn: HTTPConnection) -> str:
    return conn.url.path.removeprefix(self.prefix)

def _is_excluded_path(self, path: str) -> bool:
    return any(path.startswith(excluded) for excluded in self.exclude_paths)

def _get_token_from_headers(self, conn: HTTPConnection) -> str:
    authorization: str = conn.headers.get("Authorization")
    if not authorization:
        raise CustomUnauthorizedError

    scheme, token = get_authorization_scheme_param(authorization)
    if not (authorization and scheme and token) or scheme.lower() != "bearer":
        raise CustomUnauthorizedError

    return token

async def _get_user_from_token(self, token: str, conn: HTTPConnection) -> SystemUser:
    try:
        user = await self.auth_service.get_user_from_access_token(token)
        conn.scope["user"] = user
        return user
    except DecodeTokenException:
        raise CustomDecodeTokenError
    except ExpiredTokenException:
        raise CustomExpiredTokenError
    except Exception:
        raise CustomInvalidTokenError
