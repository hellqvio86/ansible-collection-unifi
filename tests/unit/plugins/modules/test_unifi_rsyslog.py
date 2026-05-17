from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog import run_module


def test_rsyslog_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.50",
        "port": 10516,
        "log_all_contents": True,
        "debug": False,
        "netconsole_enabled": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.UnifiAPI") as mock_api_class,
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
            ([{"_id": "rsys1", "key": "rsyslogd", "enabled": False, "ip": "", "port": 10516}], {"status": 200}),
            (
                [{"_id": "rsys1", "key": "rsyslogd", "enabled": True, "ip": "192.168.1.50", "port": 10516}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["enabled"] is True
        assert put_call[1]["data"]["ip"] == "192.168.1.50"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_rsyslog_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.50",
        "port": 10516,
        "log_all_contents": True,
        "debug": False,
        "netconsole_enabled": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.UnifiAPI") as mock_api_class,
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
                    {
                        "_id": "rsys1",
                        "key": "rsyslogd",
                        "enabled": True,
                        "ip": "192.168.1.50",
                        "port": 10516,
                        "log_all_contents": True,
                        "debug": False,
                        "netconsole_enabled": False,
                        "this_controller": False,
                        "this_controller_encrypted_only": False,
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_rsyslog_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.100",
        "port": 514,
        "log_all_contents": False,
        "debug": False,
        "netconsole_enabled": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.UnifiAPI") as mock_api_class,
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
                    {
                        "_id": "rsys1",
                        "key": "rsyslogd",
                        "enabled": True,
                        "ip": "192.168.1.50",
                        "port": 10516,
                        "log_all_contents": True,
                        "debug": False,
                        "netconsole_enabled": False,
                    }
                ],
                {"status": 200},
            ),
            (
                [
                    {
                        "_id": "rsys1",
                        "key": "rsyslogd",
                        "enabled": True,
                        "ip": "192.168.1.100",
                        "port": 514,
                        "log_all_contents": False,
                        "debug": False,
                        "netconsole_enabled": False,
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["data"]["ip"] == "192.168.1.100"
        assert put_call[1]["data"]["port"] == 514

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_rsyslog_setting_not_found():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.50",
        "port": 10516,
        "log_all_contents": True,
        "debug": False,
        "netconsole_enabled": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.UnifiAPI") as mock_api_class,
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
            ([{"_id": "ntp1", "key": "ntp"}], {"status": 200}),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "rsyslogd" in args["msg"].lower()


def test_rsyslog_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.50",
        "port": 10516,
        "log_all_contents": True,
        "debug": False,
        "netconsole_enabled": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog.UnifiAPI") as mock_api_class,
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
            ([{"_id": "rsys1", "key": "rsyslogd", "enabled": False, "ip": "", "port": 10516}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
