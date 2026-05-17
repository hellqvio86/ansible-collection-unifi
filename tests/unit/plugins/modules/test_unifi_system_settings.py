from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings import run_module


def test_system_settings_ntp_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": {
            "server_1": "0.pool.ntp.org",
            "server_2": "1.pool.ntp.org",
            "server_3": "",
            "server_4": "",
            "timezone": "Europe/Stockholm",
        },
        "mgmt": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"_id": "ntp1", "key": "ntp", "ntp_server_1": "", "ntp_server_2": "", "timezone": ""}], {"status": 200}),
            (
                [
                    {
                        "_id": "ntp1",
                        "key": "ntp",
                        "ntp_server_1": "0.pool.ntp.org",
                        "ntp_server_2": "1.pool.ntp.org",
                        "timezone": "Europe/Stockholm",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["ntp_server_1"] == "0.pool.ntp.org"
        assert put_call[1]["data"]["timezone"] == "Europe/Stockholm"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_system_settings_ntp_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": {
            "server_1": "0.pool.ntp.org",
            "timezone": "Europe/Stockholm",
        },
        "mgmt": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (
                [{"_id": "ntp1", "key": "ntp", "ntp_server_1": "0.pool.ntp.org", "timezone": "Europe/Stockholm"}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_system_settings_mgmt_disable_led():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": None,
        "mgmt": {
            "led_enabled": False,
        },
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"_id": "mgmt1", "key": "mgmt", "led_enabled": True}], {"status": 200}),
            ([{"_id": "mgmt1", "key": "mgmt", "led_enabled": False}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["data"]["led_enabled"] is False
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_system_settings_mgmt_ssh():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": None,
        "mgmt": {
            "ssh_password_enabled": False,
            "ssh_bind_wildcard": True,
        },
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (
                [{"_id": "mgmt1", "key": "mgmt", "x_ssh_auth_password_enabled": True, "x_ssh_bind_wildcard": False}],
                {"status": 200},
            ),
            (
                [{"_id": "mgmt1", "key": "mgmt", "x_ssh_auth_password_enabled": False, "x_ssh_bind_wildcard": True}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["data"]["x_ssh_auth_password_enabled"] is False
        assert put_call[1]["data"]["x_ssh_bind_wildcard"] is True
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_system_settings_both():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": {
            "server_1": "0.pool.ntp.org",
            "timezone": "Europe/Stockholm",
        },
        "mgmt": {
            "led_enabled": False,
        },
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (
                [
                    {"_id": "ntp1", "key": "ntp", "ntp_server_1": "", "timezone": ""},
                    {"_id": "mgmt1", "key": "mgmt", "led_enabled": True},
                ],
                {"status": 200},
            ),
            (
                [{"_id": "ntp1", "key": "ntp", "ntp_server_1": "0.pool.ntp.org", "timezone": "Europe/Stockholm"}],
                {"status": 200},
            ),
            ([{"_id": "mgmt1", "key": "mgmt", "led_enabled": False}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 3
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert "ntp" in kwargs["settings"]
        assert "mgmt" in kwargs["settings"]


def test_system_settings_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": {
            "server_1": "0.pool.ntp.org",
            "timezone": "Europe/Stockholm",
        },
        "mgmt": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"_id": "ntp1", "key": "ntp", "ntp_server_1": "", "timezone": ""}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert "ntp" in kwargs["settings"]


def test_system_settings_ntp_not_found():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "ntp": {
            "server_1": "0.pool.ntp.org",
        },
        "mgmt": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"_id": "mgmt1", "key": "mgmt", "led_enabled": True}], {"status": 200}),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "NTP" in args["msg"]
