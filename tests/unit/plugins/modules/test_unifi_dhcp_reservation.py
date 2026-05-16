from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation import run_module


def test_dhcp_reservation_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "02:1a:2b:3c:4d:01",
        "name": "Example Device",
        "fixed_ip": "198.51.100.71",
        "network_name": "Default",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Old Name", "use_fixedip": False}
                ],
                {"status": 200},
            ),
            # 2. Fetch networks
            (
                [{"name": "Default", "_id": "net_default"}],
                {"status": 200},
            ),
            # 3. Update client (PUT)
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Example Device", "fixed_ip": "198.51.100.71", "use_fixedip": True, "network_id": "net_default"}
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 3

        put_call = mock_api.request.call_args_list[2]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["use_fixedip"] is True
        assert put_call[1]["data"]["fixed_ip"] == "198.51.100.71"
        assert put_call[1]["data"]["network_id"] == "net_default"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["reservation"]["fixed_ip"] == "198.51.100.71"


def test_dhcp_reservation_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "02:1a:2b:3c:4d:01",
        "name": "Example Device",
        "fixed_ip": "198.51.100.71",
        "network_name": "Default",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients (already has correct reservation)
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Example Device", "use_fixedip": True, "fixed_ip": "198.51.100.71", "network_id": "net_default"}
                ],
                {"status": 200},
            ),
            # 2. Fetch networks
            (
                [{"name": "Default", "_id": "net_default"}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_dhcp_reservation_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "mac": "02:1a:2b:3c:4d:01",
        "name": None,
        "fixed_ip": None,
        "network_name": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients (has reservation)
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Example Device", "use_fixedip": True, "fixed_ip": "198.51.100.71"}
                ],
                {"status": 200},
            ),
            # 2. Remove reservation (PUT)
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Example Device", "use_fixedip": False}
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["use_fixedip"] is False

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_dhcp_reservation_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "mac": "02:1a:2b:3c:4d:01",
        "name": None,
        "fixed_ip": None,
        "network_name": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients (no reservation)
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Example Device", "use_fixedip": False}
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_dhcp_reservation_client_not_found():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Unknown Device",
        "fixed_ip": "198.51.100.99",
        "network_name": "Default",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients (empty)
            ([], {"status": 200}),
        ]

        import pytest
        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "not found" in args["msg"].lower()


def test_dhcp_reservation_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "02:1a:2b:3c:4d:01",
        "name": "Example Device",
        "fixed_ip": "198.51.100.71",
        "network_name": "Default",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            # 1. Fetch all clients
            (
                [
                    {"_id": "client1", "mac": "02:1a:2b:3c:4d:01", "name": "Old Name", "use_fixedip": False}
                ],
                {"status": 200},
            ),
            # 2. Fetch networks
            (
                [{"name": "Default", "_id": "net_default"}],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
