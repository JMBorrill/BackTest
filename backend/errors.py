"""One error shape for every failure.

    {"error": {"code": "...", "message": "...", "fields": [...]}}

`code` is the stable part: it is what the Postman tests assert on and what
a support conversation quotes. The message can be reworded without
breaking anyone.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("backtesting.api")

# Starlette raises these before any of our code runs, so they would
# otherwise return its default {"detail": ...} body.
FRAMEWORK_CODES = {404: "not_found", 405: "method_not_allowed"}


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: list[dict] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        self.headers = headers or {}


def _body(code: str, message: str, fields: list[dict] | None = None) -> dict:
    error: dict = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return {"error": error}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.code, exc.message, exc.fields),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # A body that is not JSON at all never reached the schema, so there
        # is no field to point at - that is a 400, not a 422.
        if any(error["type"] == "json_invalid" for error in exc.errors()):
            return JSONResponse(
                status_code=400,
                content=_body("invalid_json", "Request body is not valid JSON"),
            )

        fields = [
            {
                "path": ".".join(str(p) for p in error["loc"] if p != "body") or "body",
                "message": error["msg"].removeprefix("Value error, "),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("validation_failed", "Request failed validation", fields),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _framework_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(
                FRAMEWORK_CODES.get(exc.status_code, "http_error"), str(exc.detail)
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # The caller gets an id they can quote in a ticket. The traceback
        # goes to the log under the same id, and never into the response.
        request_id = f"req_{uuid.uuid4().hex[:6]}"
        log.exception("unhandled error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "request_id": request_id}},
        )
