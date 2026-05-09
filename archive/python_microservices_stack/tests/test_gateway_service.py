from python_microservices.services.gateway_service import app as gateway_app


def test_resolve_target_routes_known_api_prefixes():
    assert gateway_app.resolve_target("/api/login") == gateway_app.SERVICE_MAP["/api/login"]
    assert gateway_app.resolve_target("/api/robot/state") == gateway_app.SERVICE_MAP["/api/robot/"]
    assert gateway_app.resolve_target("/api/admin/users") == gateway_app.SERVICE_MAP["/api/admin/"]


def test_resolve_target_uses_frontend_for_non_api_paths():
    assert gateway_app.resolve_target("/") == gateway_app.FRONTEND_URL
    assert gateway_app.resolve_target("/assets/main.js") == gateway_app.FRONTEND_URL


def test_filter_headers_removes_hop_by_hop_headers():
    headers = {
        "host": "localhost",
        "content-type": "application/json",
        "connection": "keep-alive",
        "x-custom-header": "value",
    }

    filtered = gateway_app.filter_headers(headers)

    assert "host" not in filtered
    assert "connection" not in filtered
    assert filtered["content-type"] == "application/json"
    assert filtered["x-custom-header"] == "value"
