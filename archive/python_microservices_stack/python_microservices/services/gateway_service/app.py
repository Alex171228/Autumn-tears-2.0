import datetime as dt
import os

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

from python_microservices.shared.app_factory import create_service_app


app = create_service_app("Gateway Service")

SERVICE_MAP = {
    "/api/register": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/login": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/me": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/change-password": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/weather": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/robot/": os.getenv("SIMULATION_SERVICE_URL", "http://simulation-service:8000"),
    "/api/configs": os.getenv("CONFIG_SERVICE_URL", "http://config-service:8000"),
    "/api/configs/": os.getenv("CONFIG_SERVICE_URL", "http://config-service:8000"),
    "/api/data/": os.getenv("CONFIG_SERVICE_URL", "http://config-service:8000"),
    "/api/admin/": os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8000"),
}
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:80")
HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "content-encoding", "content-length", "host"}


def resolve_target(path: str) -> str:
    for prefix, target in SERVICE_MAP.items():
        if path == prefix or path.startswith(prefix):
            return target
    return FRONTEND_URL


def filter_headers(headers) -> dict:
    return {key: value for key, value in headers.items() if key.lower() not in HOP_HEADERS}


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "gateway", "time": dt.datetime.utcnow().isoformat()}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    target = resolve_target("/" + path)
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    body = await request.body()
    headers = filter_headers(request.headers)
    headers["x-forwarded-for"] = request.client.host if request.client else "unknown"
    headers["x-forwarded-proto"] = request.url.scheme
    headers["x-forwarded-host"] = request.headers.get("host", "")

    try:
        async with httpx.AsyncClient(base_url=target, timeout=120.0, follow_redirects=True) as client:
            upstream = await client.request(
                request.method,
                url,
                content=body,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Gateway error: {exc}") from exc

    response_headers = {key: value for key, value in upstream.headers.items() if key.lower() not in HOP_HEADERS}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=response_headers, media_type=upstream.headers.get("content-type"))
