"""Application error types and FastAPI exception handlers.

A single `AppError` hierarchy gives every module a consistent way to signal
failures without hand-rolling `HTTPException` + JSON shapes at each call site.
`register_exception_handlers` wires them into the app so an `AppError` raised
anywhere becomes a uniform JSON response `{"error": {"code", "message"}}`.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for expected, client-facing errors.

    Subclasses set `status_code` and a stable `code` string the frontend can
    switch on. `message` is human-readable and safe to surface.
    """

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.__name__
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


def register_exception_handlers(app: FastAPI) -> None:
    """Install the AppError -> JSON handler on the FastAPI app."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
