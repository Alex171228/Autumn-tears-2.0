from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path

        if path.startswith("/static/") or path.endswith(
            (".js", ".css", ".png", ".jpg", ".ico", ".svg", ".woff", ".woff2")
        ):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        else:
            response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"

        return response


def create_service_app(title: str) -> FastAPI:
    app = FastAPI(title=title)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CacheControlMiddleware)
    return app
