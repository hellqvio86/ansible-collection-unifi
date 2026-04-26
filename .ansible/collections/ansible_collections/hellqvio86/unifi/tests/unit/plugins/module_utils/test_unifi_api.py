import base64
import json
from unittest.mock import MagicMock, patch

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def test_unifi_api_login_success():
    module = MagicMock()
    host = "192.168.1.1"
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
    assert api.session_cookie == f"TOKEN={jwt_token}; Path=/; HttpOnly"


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
