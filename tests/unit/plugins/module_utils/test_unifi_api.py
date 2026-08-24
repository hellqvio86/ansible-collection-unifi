import base64
import json
from unittest.mock import MagicMock, patch

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def test_unifi_api_login_success():
    module = MagicMock()
    host = "192.0.2.1"
    username = "admin"
    password = "password"

    api = UnifiAPI(module, host, username, password)

    # Mock JWT payload for CSRF
    jwt_payload = json.dumps({"csrfToken": "fake-csrf-token"}).encode("utf-8")
    jwt_token = f"header.{base64.b64encode(jwt_payload).decode('utf-8')}.signature"

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"data": []}).encode("utf-8")

    mock_info = {"status": 200, "set-cookie": f"TOKEN={jwt_token}; Path=/; HttpOnly"}

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        api.login()

    assert api.csrf_token == "fake-csrf-token"
    assert api.session_cookie == f"TOKEN={jwt_token}"


def test_unifi_api_request():
    module = MagicMock()
    api = UnifiAPI(module, "host", "user", "pass")
    api.session_cookie = "cookie"
    api.csrf_token = "csrf"

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"key": "value"}).encode("utf-8")
    mock_info = {"status": 200}

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ) as mock_fetch:
        data, info = api.request("/test/path", method="POST", data={"foo": "bar"})

        assert data == {"key": "value"}
        assert info["status"] == 200
        mock_fetch.assert_called_once()
        args, kwargs = mock_fetch.call_args
        assert kwargs["method"] == "POST"
        assert json.loads(kwargs["data"]) == {"foo": "bar"}
        assert kwargs["headers"]["X-CSRF-Token"] == "csrf"


def test_unifi_api_validate_certs_default():
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")
    assert api.validate_certs is True
    assert module.params["validate_certs"] is True


def test_unifi_api_ca_path():
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(
        module, host="192.0.2.1", username="admin", password="password", ca_path="/etc/ssl/certs/custom-ca.pem"
    )
    assert api.ca_path == "/etc/ssl/certs/custom-ca.pem"
    assert module.params["ca_path"] == "/etc/ssl/certs/custom-ca.pem"


def test_unifi_api_cookie_list_parsing():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    jwt_payload = json.dumps({"csrfToken": "jwt-csrf-456"}).encode("utf-8")
    jwt_token = f"header.{base64.urlsafe_b64encode(jwt_payload).decode('utf-8')}.sig"

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": [f"TOKEN={jwt_token}; Path=/", "SESSION=session123; Path=/; Secure"],
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        api.login()

    assert api.csrf_token == "jwt-csrf-456"
    assert "TOKEN=" in api.session_cookie
    assert "SESSION=" in api.session_cookie
    assert "Path=/" not in api.session_cookie
    assert "Secure" not in api.session_cookie


def test_unifi_api_host_lock():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import _host_lock

    with _host_lock("192.0.2.1"):
        pass


def test_unifi_api_request_401_relogin_retry():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")
    api.session_cookie = "old_cookie"
    api.csrf_token = "old_csrf"

    jwt_payload = json.dumps({"csrfToken": "new_csrf"}).encode("utf-8")
    jwt_token = f"header.{base64.urlsafe_b64encode(jwt_payload).decode('utf-8')}.sig"

    mock_resp_login = MagicMock()
    mock_resp_login.read.return_value = b"{}"
    mock_login_info = {"status": 200, "set-cookie": f"TOKEN={jwt_token}"}

    mock_resp_success = MagicMock()
    mock_resp_success.read.return_value = json.dumps({"result": "ok"}).encode("utf-8")
    mock_success_info = {"status": 200}

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        side_effect=[
            (None, {"status": 401}),  # First request fails 401
            (mock_resp_login, mock_login_info),  # Re-login succeeds
            (mock_resp_success, mock_success_info),  # Retry succeeds
        ],
    ) as mock_fetch:
        data, info = api.request("/test/endpoint")
        assert data == {"result": "ok"}
        assert info["status"] == 200
        assert mock_fetch.call_count == 3
