from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info import run_module


def test_info_wifi_subset_default():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": ["wifi"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default"}], {"status": 200}),
            (
                [
                    {
                        "_id": "wlan1",
                        "name": "Home",
                        "enabled": True,
                        "security": "wpapsk",
                        "x_passphrase": "secret",
                        "networkconf_id": "net1",
                        "wlan_bands": "5g",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        info = kwargs["unifi_info"]
        assert "wifi" in info
        assert len(info["wifi"]) == 1
        assert info["wifi"][0]["network"] == "Default"


def test_info_networks():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": ["networks"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default", "purpose": "corporate", "enabled": True}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        info = kwargs["unifi_info"]
        assert "networks" in info
        assert len(info["networks"]) == 1
        assert info["networks"][0]["name"] == "Default"


def test_info_dhcp_reservations():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": ["dhcp_reservations"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default"}], {"status": 200}),
            (
                [
                    {
                        "mac": "aa:bb:cc:dd:ee:ff",
                        "name": "Printer",
                        "use_fixedip": True,
                        "fixed_ip": "192.168.1.50",
                        "network_id": "net1",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        info = kwargs["unifi_info"]
        assert "dhcp_reservations" in info
        assert len(info["dhcp_reservations"]) == 1
        assert info["dhcp_reservations"][0]["network"] == "Default"


def test_info_system_settings():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": ["system_settings"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default"}], {"status": 200}),
            (
                [
                    {"_id": "s1", "key": "ntp", "ntp_server_1": "0.pool.ntp.org", "timezone": "UTC"},
                    {"_id": "s2", "key": "mgmt", "led_enabled": True, "x_ssh_auth_password_enabled": False},
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        info = kwargs["unifi_info"]
        assert "system_settings" in info
        assert info["system_settings"]["ntp"]["server_1"] == "0.pool.ntp.org"
        assert info["system_settings"]["mgmt"]["led_enabled"] is True


def test_info_port_forward():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": ["port_forward"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default"}], {"status": 200}),
            (
                [
                    {
                        "name": "SSH",
                        "enabled": True,
                        "proto": "tcp",
                        "dst_port": "2222",
                        "fwd_port": "22",
                        "fwd_ip": "192.168.1.10",
                        "fwd_network_id": "net1",
                        "src": "",
                        "log": False,
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        info = kwargs["unifi_info"]
        assert "port_forward" in info
        assert len(info["port_forward"]) == 1
        assert info["port_forward"][0]["name"] == "SSH"
        assert info["port_forward"][0]["fwd_network"] == "Default"


def test_info_empty_subset():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "gather_subset": [],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info.UnifiAPI") as mock_api_class,
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

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        info = kwargs["unifi_info"]
        assert info == {}
