"""Bearer-token authentication.

A single shared token: the simplest scheme that still exercises a real 401
path. See the README for why that is not a production model.

A 401 carries WWW-Authenticate so a client can tell "your credentials were
rejected" from "your request was malformed".
"""
import secrets

from fastapi import Depends, Request

from backend.config import Settings, get_settings
from backend.errors import ApiError

CHALLENGE = {"WWW-Authenticate": 'Bearer realm="backtesting-api"'}


def require_token(request: Request, settings: Settings = Depends(get_settings)) -> None:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")

    # Both are 401 unauthenticated; the messages differ because the fixes do.
    # "missing" - no credentials arrived, so the request or the selected
    # environment is wrong. "invalid" - credentials arrived and did not
    # match, so only the value is wrong. Neither reveals the expected token.
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "unauthenticated", "Bearer token missing", headers=CHALLENGE)
    if not secrets.compare_digest(token.strip(), settings.api_token):
        raise ApiError(401, "unauthenticated", "Bearer token invalid", headers=CHALLENGE)
