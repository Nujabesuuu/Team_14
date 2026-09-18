from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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
