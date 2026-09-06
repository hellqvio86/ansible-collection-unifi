import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock

import pytest

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
    UnifiAPI,
    UnifiTransport,
)


class MockUniFiHandler(BaseHTTPRequestHandler):
    """Local HTTP mock server handling real TCP/HTTP round-trips for integration testing."""

    # Server state tracked across requests
    attempt_counts = {}

    def log_message(self, format, *args):
        # Silence default server logging during test run
        pass

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else ""

        if self.path == "/api/auth/login":
            creds = json.loads(body) if body else {}
            if creds.get("username") == "admin" and creds.get("password") == "secretpassword":
                # Construct a valid JWT containing csrfToken
                payload = json.dumps({"csrfToken": "extracted_csrf_token_123"}).encode("utf-8")
                token = f"header.{base64.urlsafe_b64encode(payload).decode('utf-8')}.sig"

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", f"TOKEN={token}; Path=/; HttpOnly")
                self.send_header("Set-Cookie", "SESSION=session_cookie_abc; Path=/; Secure")
                self.end_headers()
                self.wfile.write(b'{"meta": {"rc": "ok"}}')
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"meta": {"rc": "error", "msg": "Invalid credentials"}}')
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        count = MockUniFiHandler.attempt_counts.get(self.path, 0) + 1
        MockUniFiHandler.attempt_counts[self.path] = count

        if self.path == "/api/test/resource":
            # Requires valid session cookie & CSRF header
            cookie_hdr = self.headers.get("Cookie", "")
            csrf_hdr = self.headers.get("X-CSRF-Token", "")
            if "SESSION=session_cookie_abc" in cookie_hdr and csrf_hdr == "extracted_csrf_token_123":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"data": [{"id": "1", "name": "DeviceOne"}]}')
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"meta": {"rc": "error", "msg": "Unauthorized"}}')
            return

        if self.path == "/api/test/retry-401":
            # First request returns 401; subsequent requests after re-login succeed
            cookie_hdr = self.headers.get("Cookie", "")
            if count == 1 or "session_cookie_abc" not in cookie_hdr:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"meta": {"rc": "error", "msg": "Session expired"}}')
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"data": "recovered_after_relogin"}')
            return

        if self.path == "/api/test/rate-limited":
            # First request returns 429 with short Retry-After; second returns 200
            if count == 1:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "0.05")
                self.end_headers()
                self.wfile.write(b'{"meta": {"rc": "error", "msg": "Rate limit exceeded"}}')
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "rate_limit_recovered"}')
            return

        if self.path == "/api/test/always-503":
            # Always returns 503
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"meta": {"rc": "error", "msg": "Service Unavailable"}}')
            return

        self.send_response(404)
        self.end_headers()


@pytest.fixture(scope="module")
def mock_http_server():
    MockUniFiHandler.attempt_counts = {}
    server = HTTPServer(("127.0.0.1", 0), MockUniFiHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def test_integration_login_and_cookie_csrf_extraction(mock_http_server):
    """Verify real HTTP login, JWT CSRF token parsing, and authenticated request execution."""
    module = MagicMock()
    module.params = {"validate_certs": False}
    module.check_mode = False

    api = UnifiAPI(
        module,
        host=mock_http_server,
        username="admin",
        password="secretpassword",
        validate_certs=False,
    )

    # 1. Login round-trip
    success = api.login()
    assert success is True
    assert api.csrf_token == "extracted_csrf_token_123"
    assert "session_cookie_abc" in api.session_cookie

    # 2. Authenticated request using extracted credentials
    data, info = api.request("/api/test/resource")
    assert info["status"] == 200
    assert data == {"data": [{"id": "1", "name": "DeviceOne"}]}


def test_integration_401_retry_then_login_flow(mock_http_server):
    """Verify that an expired session on a 401 triggers automatic re-login and request retry over HTTP."""
    module = MagicMock()
    module.params = {"validate_certs": False}
    module.check_mode = False

    api = UnifiAPI(
        module,
        host=mock_http_server,
        username="admin",
        password="secretpassword",
        validate_certs=False,
    )

    # Initial state with an invalid/expired cookie
    api.session_cookie = "SESSION=stale_cookie"
    api.csrf_token = "stale_csrf"

    data, info = api.request("/api/test/retry-401")
    assert info["status"] == 200
    assert data == {"data": "recovered_after_relogin"}
    assert api.csrf_token == "extracted_csrf_token_123"


def test_integration_429_retry_after_header(mock_http_server):
    """Verify real HTTP 429 response respects Retry-After header and retries automatically."""
    module = MagicMock()
    module.params = {"validate_certs": False}
    module.check_mode = False

    transport = UnifiTransport(
        module,
        host=mock_http_server,
        validate_certs=False,
        retries=2,
        backoff_factor=0.01,
        rate_limit_delay=0.0,
    )

    url = f"{mock_http_server}/api/test/rate-limited"
    response, info = transport.fetch_with_retry(url, method="GET", headers={})

    assert info["status"] == 200
    assert response is not None
    body = json.loads(response.read().decode("utf-8"))
    assert body["status"] == "rate_limit_recovered"
    assert MockUniFiHandler.attempt_counts.get("/api/test/rate-limited") == 2


def test_integration_503_retry_then_give_up(mock_http_server):
    """Verify 503 on idempotent GET retries up to max configured retries with backoff and gives up."""
    module = MagicMock()
    module.params = {"validate_certs": False}
    module.check_mode = False

    transport = UnifiTransport(
        module,
        host=mock_http_server,
        validate_certs=False,
        retries=2,
        backoff_factor=0.01,
        rate_limit_delay=0.0,
    )

    url = f"{mock_http_server}/api/test/always-503"
    response, info = transport.fetch_with_retry(url, method="GET", headers={})

    assert info["status"] == 503
    # Initial attempt + 2 retries = 3 attempts total
    assert MockUniFiHandler.attempt_counts.get("/api/test/always-503") == 3
