from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server import run_module


def test_dhcp_server_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "network": "Default",
        "enabled": True,
        "dhcp_start": "192.168.1.100",
        "dhcp_stop": "192.168.1.200",
        "lease_time": 86400,
        "dns_1": "192.168.1.1",
        "dns_2": "8.8.8.8",
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
                [{"_id": "net1", "name": "Default", "dhcpd_enabled": False, "dhcpd_start": "", "dhcpd_stop": ""}],
                {"status": 200},
            ),
            (
                [
                    {
                        "_id": "net1",
                        "name": "Default",
                        "dhcpd_enabled": True,
                        "dhcpd_start": "192.168.1.100",
                        "dhcpd_stop": "192.168.1.200",
                        "dhcpd_leasetime": 86400,
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["dhcpd_enabled"] is True
        assert put_call[1]["data"]["dhcpd_start"] == "192.168.1.100"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_dhcp_server_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "network": "Default",
        "enabled": True,
        "dhcp_start": "192.168.1.100",
        "dhcp_stop": "192.168.1.200",
        "lease_time": 86400,
        "dns_1": "192.168.1.1",
        "dns_2": "8.8.8.8",
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
                        "_id": "net1",
                        "name": "Default",
                        "dhcpd_enabled": True,
                        "dhcpd_start": "192.168.1.100",
                        "dhcpd_stop": "192.168.1.200",
                        "dhcpd_leasetime": 86400,
                        "dhcpd_dns_1": "192.168.1.1",
                        "dhcpd_dns_2": "8.8.8.8",
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


def test_dhcp_server_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "network": "Default",
        "enabled": True,
        "dhcp_start": None,
        "dhcp_stop": None,
        "lease_time": None,
        "dns_1": None,
        "dns_2": None,
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
                        "_id": "net1",
                        "name": "Default",
                        "dhcpd_enabled": True,
                        "dhcpd_start": "192.168.1.100",
                        "dhcpd_stop": "192.168.1.200",
                    }
                ],
                {"status": 200},
            ),
            ([{"_id": "net1", "name": "Default", "dhcpd_enabled": False}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["data"]["dhcpd_enabled"] is False
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_dhcp_server_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "network": "Default",
        "enabled": True,
        "dhcp_start": None,
        "dhcp_stop": None,
        "lease_time": None,
        "dns_1": None,
        "dns_2": None,
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default", "dhcpd_enabled": False}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_dhcp_server_network_not_found():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "network": "NonExistent",
        "enabled": True,
        "dhcp_start": "192.168.1.100",
        "dhcp_stop": "192.168.1.200",
        "lease_time": None,
        "dns_1": None,
        "dns_2": None,
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
            ([], {"status": 200}),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "not found" in args["msg"].lower()


def test_dhcp_server_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "network": "Default",
        "enabled": True,
        "dhcp_start": "192.168.1.100",
        "dhcp_stop": "192.168.1.200",
        "lease_time": 86400,
        "dns_1": "192.168.1.1",
        "dns_2": "8.8.8.8",
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
            (
                [{"_id": "net1", "name": "Default", "dhcpd_enabled": False, "dhcpd_start": "", "dhcpd_stop": ""}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_dhcp_server_update_single_field():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "network": "Default",
        "enabled": True,
        "dhcp_start": "192.168.1.100",
        "dhcp_stop": "192.168.1.200",
        "lease_time": 86400,
        "dns_1": "1.1.1.1",
        "dns_2": None,
        "gateway": None,
        "domain": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server.UnifiAPI") as mock_api_class,
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
                        "_id": "net1",
                        "name": "Default",
                        "dhcpd_enabled": True,
                        "dhcpd_start": "192.168.1.100",
                        "dhcpd_stop": "192.168.1.200",
                        "dhcpd_leasetime": 86400,
                        "dhcpd_dns_1": "8.8.8.8",
                        "dhcpd_dns_2": "",
                    }
                ],
                {"status": 200},
            ),
            (
                [
                    {
                        "_id": "net1",
                        "name": "Default",
                        "dhcpd_enabled": True,
                        "dhcpd_start": "192.168.1.100",
                        "dhcpd_stop": "192.168.1.200",
                        "dhcpd_leasetime": 86400,
                        "dhcpd_dns_1": "1.1.1.1",
                        "dhcpd_dns_2": "",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["data"]["dhcpd_dns_1"] == "1.1.1.1"
        assert put_call[1]["data"]["dhcpd_enabled"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
