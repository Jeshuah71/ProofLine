import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app, limiter, MAX_REQUEST_BODY_SIZE


FRONTEND_ORIGIN = "https://proofline.jeshuah024.workers.dev"
ALLOWED_ORIGINS = [
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
ENDPOINTS = [
    ("/health", "GET", None),
    ("/analyze", "POST", {"message": "To start your new job, pay $250."}),
    ("/analyze-url", "POST", {"url": "https://example.com/jobs"}),
    ("/analyze-posting", "POST", {
        "title": "Developer",
        "description": "We are hiring a developer.",
    }),
]


@pytest.fixture
def client():
    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    limiter.reset()


@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
@pytest.mark.parametrize("path,method,payload", ENDPOINTS)
def test_allowed_preflight(client, origin, path, method, payload):
    response = client.options(path, headers={
        "Origin": origin,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "content-type",
    })

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert method in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize("path,method,payload", ENDPOINTS)
def test_endpoint_response_has_cors_and_privacy_headers(client, path, method, payload):
    response = client.request(method, path, json=payload, headers={
        "Origin": FRONTEND_ORIGIN,
    })

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    data = response.json()
    if path == "/health":
        assert data == {"status": "ok"}
    elif path == "/analyze":
        assert data["warning_count"] == 1
        assert data["assessment"] == "Review recommended"
    elif path == "/analyze-url":
        assert data["status"] == "checked"
        assert data["hostname"] == "example.com"
    else:
        assert {"prediction", "model_score", "threshold", "scope",
                "rule_signals", "review_recommended"} <= data.keys()


@pytest.mark.parametrize("origin", [
    "https://untrusted.example",
    "https://proofline.jeshuah024.workers.dev.attacker.example",
    "null",
])
def test_disallowed_origin(client, origin):
    response = client.options("/analyze", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("method,header", [
    ("DELETE", "content-type"),
    ("POST", "x-unapproved-header"),
])
def test_disallowed_preflight_method_or_header(client, method, header):
    response = client.options("/analyze", headers={
        "Origin": FRONTEND_ORIGIN,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": header,
    })
    assert response.status_code == 400


def test_validation_and_body_limit_responses_have_cors(client):
    for message, expected_status in [
        ("", 422),
        ("x" * (MAX_REQUEST_BODY_SIZE + 1), 413),
    ]:
        response = client.post("/analyze", json={"message": message}, headers={
            "Origin": FRONTEND_ORIGIN,
        })
        assert response.status_code == expected_status
        assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_rate_limit_response_has_cors_and_privacy_headers(client):
    for _ in range(21):
        response = client.post("/analyze", json={"message": "Interview invitation."},
                               headers={"Origin": FRONTEND_ORIGIN})
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_missing_model_response_has_cors(client, monkeypatch, tmp_path):
    monkeypatch.setattr("main.MODEL_PATH", tmp_path / "missing.joblib")
    response = client.post("/analyze-posting", json={"description": "Job posting."},
                           headers={"Origin": FRONTEND_ORIGIN})
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


@pytest.mark.parametrize("payment", ["pay $250", "send $25.50", "transfer $100"])
def test_payment_amount_regex(client, payment):
    response = client.post("/analyze", json={
        "message": f"To start your new job, {payment}.",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["warnings"] == [f"Payment Requests: possible payment of {payment}"]
    assert data["warning_count"] == 1
    assert data["assessment"] == "Review recommended"


@pytest.mark.parametrize("configured_origin,expected_origin", [
    (None, FRONTEND_ORIGIN),
    ("   ", FRONTEND_ORIGIN),
    (" https://custom.example/ ", "https://custom.example"),
])
def test_origin_environment_configuration(configured_origin, expected_origin):
    # Import in a fresh process without changing the shared app or its limiter.
    env = os.environ.copy()
    env.pop("PROOFLINE_FRONTEND_ORIGIN", None)
    if configured_origin is not None:
        env["PROOFLINE_FRONTEND_ORIGIN"] = configured_origin
    result = subprocess.run(
        [sys.executable, "-c",
         "import json; from main import allowed_origins; print(json.dumps(allowed_origins))"],
        cwd=Path(__file__).resolve().parent,
        env=env, capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == [
        "http://localhost:5173", "http://127.0.0.1:5173", expected_origin,
    ]
