from unittest.mock import patch

import pytest

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login import run_module


def test_login_success():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.login.return_value = True
        mock_api.session_cookie = "unifises=mock_cookie_val"
        mock_api.csrf_token = "mock_csrf_val"
        mock_api.request.return_value = (
            {"data": [{"name": "default", "desc": "Default", "role": "admin"}]},
            {"status": 200},
        )

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert "unifi_session" in kwargs
        session = kwargs["unifi_session"]
        assert session["session_cookie"] == "unifises=mock_cookie_val"
        assert session["csrf_token"] == "mock_csrf_val"
        assert session["site"] == "default"
        assert session["host"] == "192.0.2.1"
        assert len(session["sites"]) == 1
        assert session["sites"][0]["name"] == "default"


def test_login_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True

        run_module()

        mock_api_class.assert_not_called()
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert kwargs["unifi_session"]["session_cookie"] == "check-mode-cookie"


def test_login_failure():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "wrongpassword",
        "site": "default",
        "validate_certs": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.login.return_value = False

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "login failed" in mock_module.fail_json.call_args[1]["msg"]
