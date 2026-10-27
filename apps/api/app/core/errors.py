import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Framework-level errors (unknown route, wrong method) get the same {code, detail} envelope.
_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
    429: "RATE_LIMITED",
}


class ApiError(Exception):
    """Domain/API error carrying a stable machine-readable code."""

    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {
                # loc is ("body", "title") / ("query", "limit"); the first part is noise for the client.
                "field": ".".join(str(p) for p in err["loc"][1:]) or str(err["loc"][0]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        detail = "; ".join(f"{f['field']}: {f['message']}" for f in fields) or "Invalid request"
        return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "detail": detail, "fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, f"HTTP_{exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code, "detail": str(exc.detail)},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "detail": "Something went wrong"})


# Shortcuts used across services
def not_found(what: str) -> ApiError:
    return ApiError(404, f"{what.upper()}_NOT_FOUND", f"{what} not found")


def forbidden(code: str = "FORBIDDEN", detail: str = "Not allowed") -> ApiError:
    return ApiError(403, code, detail)


def conflict(code: str, detail: str) -> ApiError:
    return ApiError(409, code, detail)


def unprocessable(code: str, detail: str) -> ApiError:
    return ApiError(422, code, detail)


def premium_required() -> ApiError:
    return ApiError(402, "PREMIUM_REQUIRED", "This feature requires Teamate+")
