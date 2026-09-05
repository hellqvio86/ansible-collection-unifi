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


def test_unifi_api_validate_certs_default(monkeypatch):
    monkeypatch.delenv("UNIFI_VALIDATE_CERTS", raising=False)
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")
    assert api.validate_certs is True
    assert module.params["validate_certs"] is True
    module.warn.assert_not_called()


def test_unifi_api_validate_certs_explicit_false():
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password", validate_certs=False)
    assert api.validate_certs is False
    assert module.params["validate_certs"] is False
    module.warn.assert_called_once()
    assert "insecure" in module.warn.call_args[0][0].lower()


def test_unifi_api_validate_certs_explicit_true():
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password", validate_certs=True)
    assert api.validate_certs is True
    assert module.params["validate_certs"] is True
    module.warn.assert_not_called()


def test_unifi_api_validate_certs_env_fallback(monkeypatch):
    monkeypatch.setenv("UNIFI_VALIDATE_CERTS", "false")
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")
    assert api.validate_certs is False
    assert module.params["validate_certs"] is False
    module.warn.assert_called_once()

    monkeypatch.setenv("UNIFI_VALIDATE_CERTS", "true")
    module_true = MagicMock()
    module_true.params = {}
    api_true = UnifiAPI(module_true, host="192.0.2.1", username="admin", password="password")
    assert api_true.validate_certs is True
    module_true.warn.assert_not_called()


def test_unifi_api_validate_certs_explicit_overrides_env(monkeypatch):
    # Explicit True overrides UNIFI_VALIDATE_CERTS=false
    monkeypatch.setenv("UNIFI_VALIDATE_CERTS", "false")
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password", validate_certs=True)
    assert api.validate_certs is True
    assert module.params["validate_certs"] is True
    module.warn.assert_not_called()

    # Explicit False overrides UNIFI_VALIDATE_CERTS=true
    monkeypatch.setenv("UNIFI_VALIDATE_CERTS", "true")
    module2 = MagicMock()
    module2.params = {}
    api2 = UnifiAPI(module2, host="192.0.2.1", username="admin", password="password", validate_certs=False)
    assert api2.validate_certs is False
    assert module2.params["validate_certs"] is False
    module2.warn.assert_called_once()


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


def test_unifi_api_login_direct_header_csrf():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": "SESSION=sess123; Path=/; HttpOnly",
        "X-CSRF-Token": "direct-header-csrf-token",
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        assert api.login() is True

    assert api.csrf_token == "direct-header-csrf-token"
    assert api.session_cookie == "SESSION=sess123"


def test_unifi_api_login_body_csrf():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"csrfToken": "direct-body-csrf-token"}).encode("utf-8")
    mock_info = {
        "status": 200,
        "set-cookie": "SESSION=sess456; Path=/",
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        assert api.login() is True

    assert api.csrf_token == "direct-body-csrf-token"


def test_unifi_api_login_dedicated_cookie_csrf():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": ["SESSION=sess789; Path=/", "csrf_token=cookie-csrf-value; Path=/; Secure"],
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        assert api.login() is True

    assert api.csrf_token == "cookie-csrf-value"


def test_unifi_api_login_cookie_attributes_parsing():
    module = MagicMock()
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": [
            "TOKEN=tok123; Path=/; Domain=.local; Expires=Wed, 21 Oct 2026 07:28:00 GMT; HttpOnly; SameSite=Lax",
            "csrf_token=csrf123; Path=/; Secure",
        ],
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        assert api.login() is True

    assert "Path=/" not in api.session_cookie
    assert "Expires=" not in api.session_cookie
    assert "HttpOnly" not in api.session_cookie
    assert "SameSite=" not in api.session_cookie
    assert "TOKEN=tok123" in api.session_cookie
    assert "csrf_token=csrf123" in api.session_cookie


def test_unifi_api_login_malformed_jwt_fails():
    import pytest

    module = MagicMock()
    module.fail_json.side_effect = Exception("fail_json")
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": "TOKEN=not.a.valid.jwt; Path=/",
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        with pytest.raises(Exception, match="fail_json"):
            api.login()

    assert module.fail_json.called
    assert "failed to extract csrf" in module.fail_json.call_args[1]["msg"].lower()


def test_unifi_api_login_missing_csrf_fails():
    import pytest

    module = MagicMock()
    module.fail_json.side_effect = Exception("fail_json")
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password")

    mock_response = MagicMock()
    mock_response.read.return_value = b"{}"
    mock_info = {
        "status": 200,
        "set-cookie": "SESSION=sess123; Path=/",
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ):
        with pytest.raises(Exception, match="fail_json"):
            api.login()

    assert module.fail_json.called
    assert "failed to extract csrf" in module.fail_json.call_args[1]["msg"].lower()


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


def test_unifi_api_token_auth():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import AuthMode

    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", api_key="secret-api-token-123")

    assert api.auth_mode == AuthMode.API_KEY
    assert api.api_key == "secret-api-token-123"

    # login() should return True immediately without any HTTP request
    with patch("ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url") as mock_fetch:
        assert api.login() is True
        mock_fetch.assert_not_called()

    # request() should use X-API-KEY and omit Cookie / X-CSRF-Token
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"devices": []}).encode("utf-8")
    mock_info = {"status": 200}

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(mock_response, mock_info),
    ) as mock_fetch:
        data, info = api.request("/proxy/network/v2/api/site/default/device")
        assert data == {"devices": []}
        assert info["status"] == 200
        mock_fetch.assert_called_once()
        _, kwargs = mock_fetch.call_args
        assert kwargs["headers"]["X-API-KEY"] == "secret-api-token-123"
        assert "Cookie" not in kwargs["headers"]
        assert "X-CSRF-Token" not in kwargs["headers"]


def test_unifi_api_token_env_fallback(monkeypatch):
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import AuthMode

    monkeypatch.setenv("UNIFI_API_KEY", "env-api-key-456")
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1")
    assert api.auth_mode == AuthMode.API_KEY
    assert api.api_key == "env-api-key-456"

    # UNIFI_API_TOKEN fallback
    monkeypatch.delenv("UNIFI_API_KEY")
    monkeypatch.setenv("UNIFI_API_TOKEN", "env-token-789")
    api2 = UnifiAPI(module, host="192.0.2.1")
    assert api2.auth_mode == AuthMode.API_KEY
    assert api2.api_key == "env-token-789"


def test_unifi_api_token_precedence_over_user_pass():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import AuthMode

    module = MagicMock()
    module.params = {}
    # Even if username and password are provided, api_key takes precedence
    api = UnifiAPI(module, host="192.0.2.1", username="admin", password="password", api_key="primary-api-token")
    assert api.auth_mode == AuthMode.API_KEY
    with patch("ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url") as mock_fetch:
        assert api.login() is True
        mock_fetch.assert_not_called()


def test_unifi_api_token_401_no_relogin():
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", api_key="invalid-token")

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(None, {"status": 401, "msg": "Unauthorized"}),
    ) as mock_fetch:
        data, info = api.request("/proxy/network/api/s/default/stat/device")
        assert data is None
        assert info["status"] == 401
        # Exactly 1 request made; no relogin attempted
        assert mock_fetch.call_count == 1


def test_unifi_api_no_credentials_fail():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import AuthMode

    module = MagicMock()
    module.params = {}
    module.fail_json.side_effect = Exception("fail_json")
    api = UnifiAPI(module, host="192.0.2.1")

    assert api.auth_mode == AuthMode.NONE
    import pytest

    with pytest.raises(Exception, match="fail_json"):
        api.login()
    assert module.fail_json.called
    fail_msg = module.fail_json.call_args[1]["msg"]
    assert "api_key" in fail_msg


def test_unifi_api_sanitize_info():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import _sanitize_info

    info = {
        "status": 200,
        "set-cookie": "TOKEN=jwt.token.here",
        "Cookie": "session=secret",
        "X-API-KEY": "secret-key",
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }
    sanitized = _sanitize_info(info)
    assert sanitized["status"] == 200
    assert sanitized["Content-Type"] == "application/json"
    assert sanitized["set-cookie"] == "********"
    assert sanitized["Cookie"] == "********"
    assert sanitized["X-API-KEY"] == "********"
    assert sanitized["Authorization"] == "********"


def test_sanitize_api_error_structure():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import sanitize_api_error

    raw_info = {
        "status": 401,
        "msg": "HTTP Error 401: Unauthorized",
        "url": "https://192.168.1.1/api/auth/login?token=supersecret123",
        "set-cookie": "TOKEN=ey...; Path=/; HttpOnly",
        "Set-Cookie": "session=secret",
        "Cookie": "session=secret",
        "Authorization": "Bearer tok_12345",
        "body": '{"meta": {"rc": "error", "msg": "Invalid credentials for user admin"}}',
    }
    err = sanitize_api_error(raw_info, endpoint="/api/auth/login")

    # Verify only safe keys are returned
    assert set(err.keys()) == {"status", "category", "endpoint_category", "msg"}
    assert err["status"] == 401
    assert err["category"] == "auth"
    assert err["endpoint_category"] == "auth"
    assert err["msg"] == "Invalid credentials for user admin"

    # Verify sensitive data/headers are excluded
    assert "set-cookie" not in err
    assert "Set-Cookie" not in err
    assert "Cookie" not in err
    assert "Authorization" not in err
    assert "url" not in err
    assert "body" not in err
    assert "supersecret123" not in str(err)
    assert "tok_12345" not in str(err)


def test_sanitize_api_error_extracts_safe_controller_msg():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import sanitize_api_error

    # Test meta.msg extraction
    info_meta = {
        "status": 400,
        "body": '{"meta": {"rc": "error", "msg": "api.err.InvalidPayload"}}',
    }
    assert sanitize_api_error(info_meta)["msg"] == "api.err.InvalidPayload"

    # Test message extraction
    info_message = {
        "status": 403,
        "body": '{"message": "Permission denied for resource"}',
    }
    assert sanitize_api_error(info_message)["msg"] == "Permission denied for resource"

    # Test non-JSON HTML body fallback to info.msg (never leaking HTML body)
    info_html = {
        "status": 502,
        "msg": "Bad Gateway",
        "body": "<html><body>502 Server internal error with sensitive stack trace</body></html>",
    }
    err_html = sanitize_api_error(info_html)
    assert err_html["msg"] == "Bad Gateway"
    assert "sensitive stack trace" not in str(err_html)


def test_sanitize_api_error_endpoint_categorization():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import categorize_endpoint

    assert categorize_endpoint("/api/auth/login") == "auth"
    assert categorize_endpoint("/proxy/network/v2/api/site/default/firewall-policies") == "firewall"
    assert categorize_endpoint("/proxy/network/api/s/default/rest/wlanconf") == "wlan"
    assert categorize_endpoint("/proxy/network/api/s/default/rest/networkconf") == "network"
    assert categorize_endpoint("/proxy/network/api/s/default/rest/portconf") == "port_profile"
    assert categorize_endpoint("/proxy/network/api/s/default/rest/portforward") == "port_forward"
    assert categorize_endpoint("/api/userCertificates") == "certificate"
    assert categorize_endpoint("/proxy/network/api/s/default/stat/alluser") == "client"
    assert categorize_endpoint("/proxy/network/api/s/default/stat/device") == "device"
    assert categorize_endpoint("/api/system/settings") == "system"
    assert categorize_endpoint("/unknown/path") == "api"
    assert categorize_endpoint(None) == "general"


def test_scrub_secrets():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import scrub_secrets

    # Known secrets
    text = "Failed with password=supersecretpass and token: my_secret_token"
    scrubbed = scrub_secrets(text, secrets=["supersecretpass", "my_secret_token"])
    assert "supersecretpass" not in scrubbed
    assert "my_secret_token" not in scrubbed
    assert "********" in scrubbed

    # Private key scrubbing
    pem = (
        "Error loading key: -----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0m4wz...\n"
        "-----END RSA PRIVATE KEY-----\n"
        "Invalid format"
    )
    scrubbed_pem = scrub_secrets(pem)
    assert "BEGIN RSA PRIVATE KEY" not in scrubbed_pem
    assert "[PRIVATE KEY REDACTED]" in scrubbed_pem

    # Bearer and JWT scrubbing
    jwt = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN"
    scrubbed_jwt = scrub_secrets(jwt)
    assert "eyJ" not in scrubbed_jwt
    assert "Bearer ********" in scrubbed_jwt


def test_api_login_failure_never_leaks_injected_password():
    from unittest.mock import MagicMock, patch

    import pytest

    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    fake_password = "deliberately_injected_super_secret_password_12345!"
    fake_token = "deliberately_injected_cookie_token_99999"

    module = MagicMock()
    module.fail_json.side_effect = Exception("fail_json called")
    module.params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": fake_password,
        "validate_certs": True,
    }

    api = UnifiAPI(module)

    mock_fail_info = {
        "status": 401,
        "msg": f"HTTP Error 401: Unauthorized for password {fake_password}",
        "set-cookie": f"TOKEN={fake_token}; Path=/; HttpOnly",
        "Cookie": f"TOKEN={fake_token}",
        "body": f'{{"message": "Login failed for password {fake_password}"}}',
    }

    with patch("ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url") as mock_fetch:
        mock_fetch.return_value = (None, mock_fail_info)
        with pytest.raises(Exception, match="fail_json called"):
            api.login()

    assert module.fail_json.called
    call_kwargs = module.fail_json.call_args[1]

    output_str = str(call_kwargs)
    assert fake_password not in output_str, "Injected password leaked in login failure output!"
    assert fake_token not in output_str, "Injected cookie token leaked in login failure output!"
    assert "set-cookie" not in output_str
    assert "Cookie" not in output_str
    assert call_kwargs["info"]["status"] == 401
    assert call_kwargs["info"]["category"] == "auth"


def test_api_request_failure_never_leaks_injected_api_key():
    from unittest.mock import MagicMock, patch

    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    fake_api_key = "deliberately_injected_api_key_TOKEN_ABCXYZ"

    module = MagicMock()
    module.params = {
        "host": "192.168.1.1",
        "api_key": fake_api_key,
        "validate_certs": True,
    }

    api = UnifiAPI(module)

    mock_fail_info = {
        "status": 400,
        "msg": f"HTTP Error 400: Bad Request with api_key={fake_api_key}",
        "X-API-KEY": fake_api_key,
        "body": f'{{"meta": {{"rc": "error", "msg": "Invalid request using key {fake_api_key}"}}}}',
    }

    with patch("ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url") as mock_fetch:
        mock_fetch.return_value = (None, mock_fail_info)
        res, info = api.request("/proxy/network/api/s/default/rest/wlanconf")

    assert res is None
    info_str = str(info)
    assert fake_api_key not in info_str, "Injected API key leaked in request failure info!"
    assert "X-API-KEY" not in info
    assert info["status"] == 400
    assert info["category"] == "wlan"
    assert info["endpoint_category"] == "wlan"
    assert "********" in info["msg"]


def test_unifi_api_check_mode_mutation_blocked():
    from unittest.mock import MagicMock

    import pytest

    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    module = MagicMock()
    module.check_mode = True
    module.params = {"host": "192.168.1.1", "api_key": "test-key"}
    module.fail_json.side_effect = Exception("fail_json called")

    api = UnifiAPI(module)

    # Calling POST in check mode must fail and block mutation
    with pytest.raises(Exception, match="fail_json called"):
        api.request("/proxy/network/api/s/default/rest/wlanconf", method="POST", data={"name": "test"})

    module.fail_json.assert_called_once()
    assert "mutating request POST" in module.fail_json.call_args[1]["msg"]

    # Calling DELETE in check mode must fail and block mutation
    module.fail_json.reset_mock()
    with pytest.raises(Exception, match="fail_json called"):
        api.request("/proxy/network/api/s/default/rest/wlanconf/123", method="DELETE")

    module.fail_json.assert_called_once()
    assert "mutating request DELETE" in module.fail_json.call_args[1]["msg"]


def test_unifi_api_sanitize_diff():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import make_diff, sanitize_diff

    sanitized = sanitize_diff({"token": "secret123", "normal": "val"})
    assert sanitized["token"] == "********"
    assert sanitized["normal"] == "val"

    before = {
        "name": "WLAN1",
        "passphrase": "super_secret_wifi_password",
        "x_passphrase": "super_secret_wifi_password",
        "enabled": True,
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgk...",
    }
    after = {
        "name": "WLAN1_Updated",
        "passphrase": "new_super_secret_wifi_password",
        "x_passphrase": "new_super_secret_wifi_password",
        "enabled": True,
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgk...",
    }

    diff = make_diff(before, after)

    assert diff["before"]["name"] == "WLAN1"
    assert diff["before"]["passphrase"] == "********"
    assert diff["before"]["x_passphrase"] == "********"
    assert diff["before"]["private_key"] == "********"
    assert diff["before"]["enabled"] is True

    assert diff["after"]["name"] == "WLAN1_Updated"
    assert diff["after"]["passphrase"] == "********"
    assert diff["after"]["x_passphrase"] == "********"
    assert diff["after"]["private_key"] == "********"
    assert "super_secret" not in str(diff)


def test_unifi_endpoints():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiEndpoints

    assert UnifiEndpoints.auth_login() == "/api/auth/login"
    assert UnifiEndpoints.user_certificates() == "/api/userCertificates"
    assert UnifiEndpoints.user_certificates("123") == "/api/userCertificates/123"
    assert UnifiEndpoints.wlan("default") == "/proxy/network/api/s/default/rest/wlanconf"
    assert UnifiEndpoints.wlan("default", "abc") == "/proxy/network/api/s/default/rest/wlanconf/abc"
    assert UnifiEndpoints.port_profile("default") == "/proxy/network/api/s/default/rest/portconf"
    assert UnifiEndpoints.network_conf("default") == "/proxy/network/api/s/default/rest/networkconf"
    assert UnifiEndpoints.user("default") == "/proxy/network/api/s/default/rest/user"
    assert UnifiEndpoints.device("default") == "/proxy/network/api/s/default/stat/device"
    assert UnifiEndpoints.port_forward("default") == "/proxy/network/api/s/default/rest/portforward"
    assert UnifiEndpoints.firewall_group("default") == "/proxy/network/api/s/default/rest/firewallgroup"
    assert UnifiEndpoints.firewall_zone("default") == "/proxy/network/v2/api/site/default/firewall-zone"
    assert UnifiEndpoints.firewall_policy("default") == "/proxy/network/v2/api/site/default/firewall-rule"
    assert UnifiEndpoints.nat_rule("default") == "/proxy/network/v2/api/site/default/nat/rule"
    assert UnifiEndpoints.setting("mgmt", "default") == "/proxy/network/api/s/default/rest/setting/mgmt"


def test_unifi_transport_methods():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiTransport

    assert UnifiTransport.is_safe_method("GET") is True
    assert UnifiTransport.is_safe_method("HEAD") is True
    assert UnifiTransport.is_safe_method("OPTIONS") is True
    assert UnifiTransport.is_safe_method("POST") is False
    assert UnifiTransport.is_safe_method("PUT") is False
    assert UnifiTransport.is_safe_method("DELETE") is False

    assert UnifiTransport.is_idempotent_method("GET") is True
    assert UnifiTransport.is_idempotent_method("PUT") is True
    assert UnifiTransport.is_idempotent_method("DELETE") is True
    assert UnifiTransport.is_idempotent_method("POST") is False


def test_unifi_transport_retry_policy():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiTransport

    transport = UnifiTransport(module=MagicMock(), host="192.0.2.1")

    # 429 is retryable across all methods
    assert transport.should_retry("GET", 429) is True
    assert transport.should_retry("PUT", 429) is True
    assert transport.should_retry("POST", 429) is True
    assert transport.should_retry("DELETE", 429) is True

    # 502/503/504 are retryable for GET/PUT/DELETE
    assert transport.should_retry("GET", 502) is True
    assert transport.should_retry("PUT", 503) is True
    assert transport.should_retry("DELETE", 504) is True

    # Critical: Non-idempotent POST is NOT retried on 500/502/503/504 to prevent duplicates!
    assert transport.should_retry("POST", 500) is False
    assert transport.should_retry("POST", 502) is False
    assert transport.should_retry("POST", 503) is False
    assert transport.should_retry("POST", 504) is False

    # But login POST is safe to retry on 502/503
    assert transport.should_retry("POST", 502, is_login=True) is True
    assert transport.should_retry("POST", 503, is_login=True) is True

    # 400, 401, 404, etc. are not retryable
    assert transport.should_retry("GET", 400) is False
    assert transport.should_retry("GET", 404) is False


def test_unifi_transport_post_mutation_not_retried_on_server_error():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", api_key="test-key")

    mock_info_503 = {"status": 503, "msg": "Service Unavailable"}

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(None, mock_info_503),
    ) as mock_fetch:
        data, info = api.request("/proxy/network/api/s/default/rest/wlanconf", method="POST", data={"name": "NewWlan"})
        assert data is None
        assert info["status"] == 503
        # Exactly 1 call: POST must not be retried on 503 to avoid creating duplicate WLANs!
        assert mock_fetch.call_count == 1


def test_unifi_transport_retry_after_header():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiTransport

    transport = UnifiTransport(module=MagicMock(), host="192.0.2.1", retries=2)

    mock_resp_429 = (None, {"status": 429, "retry-after": "0.1"})
    mock_resp_200 = (MagicMock(read=lambda: b'{"ok": true}'), {"status": 200})

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        side_effect=[mock_resp_429, mock_resp_200],
    ) as mock_fetch:
        with patch("time.sleep") as mock_sleep:
            resp, info = transport.fetch_with_retry("https://192.0.2.1/test", "GET", {})
            assert info["status"] == 200
            assert mock_fetch.call_count == 2
            mock_sleep.assert_any_call(0.1)


def test_unifi_transport_lock_timeout_fallback():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiTransport

    module = MagicMock()
    transport = UnifiTransport(module=module, host="192.0.2.1", lock_timeout=0.05)

    with patch("fcntl.flock", side_effect=BlockingIOError):
        with transport.host_lock():
            pass
    module.warn.assert_called_once()
    assert "timed out" in module.warn.call_args[0][0]


def test_unifi_api_timeout_configuration(monkeypatch):
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    # 1. Default timeout is 30
    module = MagicMock()
    module.params = {}
    api = UnifiAPI(module, host="192.0.2.1", api_key="key")
    assert api.timeout == 30
    assert module.params["timeout"] == 30

    # 2. Explicit timeout argument
    module2 = MagicMock()
    module2.params = {}
    api2 = UnifiAPI(module2, host="192.0.2.1", api_key="key", timeout=45)
    assert api2.timeout == 45
    assert module2.params["timeout"] == 45

    # 3. Environment variable fallback
    monkeypatch.setenv("UNIFI_TIMEOUT", "60")
    module3 = MagicMock()
    module3.params = {}
    api3 = UnifiAPI(module3, host="192.0.2.1", api_key="key")
    assert api3.timeout == 60
    assert module3.params["timeout"] == 60

    # 4. Propagation to fetch_url
    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api.fetch_url",
        return_value=(MagicMock(read=lambda: b"{}"), {"status": 200}),
    ) as mock_fetch:
        api3.request("/test")
        _, kwargs = mock_fetch.call_args
        assert kwargs["timeout"] == 60


def test_unifi_compatibility_version_parsing():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
        ControllerVersion,
        UnifiCompatibility,
    )

    v1 = ControllerVersion("8.1.113")
    assert v1.major == 8 and v1.minor == 1 and v1.patch == 113
    assert v1 >= (8, 0, 0)
    assert v1 >= ControllerVersion("8.0.28")
    assert v1 < ControllerVersion("8.2.0")

    v_old = ControllerVersion("7.5.176")
    assert v_old < (8, 0, 0)

    # None handling
    assert UnifiCompatibility.parse_version(None) is None


def test_unifi_compatibility_checks():
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiCompatibility

    # Policy engine requires Network 8.0.0+
    ok, err = UnifiCompatibility.check_policy_engine_support("8.0.28")
    assert ok is True and err is None

    ok, err = UnifiCompatibility.check_policy_engine_support("7.5.176")
    assert ok is False and "does not support the Policy Engine" in err

    # User certificate requires UniFi OS 3.0.0+
    ok, err = UnifiCompatibility.check_user_certificate_support("3.2.12")
    assert ok is True and err is None

    ok, err = UnifiCompatibility.check_user_certificate_support("2.5.17")
    assert ok is False and "does not support user certificate management" in err


def test_unifi_api_validate_feature_support():
    import pytest

    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

    module = MagicMock()
    module.fail_json.side_effect = Exception("fail_json called")
    api = UnifiAPI(module, host="192.0.2.1", api_key="key")

    # Mock controller returning Network 7.4.156
    with patch.object(api, "get_network_version", return_value="7.4.156"):
        with pytest.raises(Exception, match="fail_json called"):
            api.validate_feature_support("policy_engine")
        module.fail_json.assert_called_once()
        assert "Policy Engine" in module.fail_json.call_args[1]["msg"]

    # Mock controller returning Network 8.1.113
    module.fail_json.reset_mock()
    with patch.object(api, "get_network_version", return_value="8.1.113"):
        api.validate_feature_support("policy_engine")
        module.fail_json.assert_not_called()



