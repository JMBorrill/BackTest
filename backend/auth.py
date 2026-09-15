"""Bearer-token authentication.

A single shared token, chosen because it is the simplest scheme that still
exercises a real 401 path. It is a demonstration model only. It is not how
any particular payments provider authenticates, and nothing here should be
copied into a real integration - those follow the provider's own current
documentation, key management and access controls.

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

    # Both cases are 401 with code "unauthenticated", but the messages differ
    # deliberately, because they point at different problems:
    #
    #   "missing" - no usable Authorization header arrived. The integration
    #               is not sending credentials at all, so the fault is in
    #               how the request is built or which environment is selected.
    #   "invalid" - a token arrived and did not match. The wiring is correct
    #               and only the value is wrong, which is usually a stale or
    #               rotated secret.
    #
    # That single word is what lets first-line support tell those apart from
    # the response alone. Neither message reveals anything about the expected
    # token, so it costs nothing against someone guessing.
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "unauthenticated", "Bearer token missing", headers=CHALLENGE)
    if not secrets.compare_digest(token.strip(), settings.api_token):
        raise ApiError(401, "unauthenticated", "Bearer token invalid", headers=CHALLENGE)
