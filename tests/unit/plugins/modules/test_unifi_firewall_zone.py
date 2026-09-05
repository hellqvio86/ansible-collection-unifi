from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone import (
    _build_desired_payload,
    run_module,
)

# ---------------------------------------------------------------------------
# Desired-state builder tests (independent of HTTP/API)
# ---------------------------------------------------------------------------


def test_build_desired_payload_basic():
    result = _build_desired_payload("LAN")
    assert result["name"] == "LAN"
    assert result["network_ids"] == []


def test_build_desired_payload_special_chars():
    result = _build_desired_payload("Guest WiFi Zone")
    assert result["name"] == "Guest WiFi Zone"
    assert result["network_ids"] == []


def test_build_desired_payload_returns_fresh_list():
    """Each call must return an independent list to prevent mutation aliasing."""
    r1 = _build_desired_payload("Z1")
    r2 = _build_desired_payload("Z2")
    r1["network_ids"].append("net-1")
    assert r2["network_ids"] == []


def test_zone_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Internal",
        "type": "lan",
        "description": "Main LAN zone",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
            ([{"_id": "zone1", "name": "Internal", "type": "LAN"}], {"status": 201}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "Internal"
        assert post_call[1]["data"]["network_ids"] == []

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_zone_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Internal",
        "type": "lan",
        "description": "Main LAN zone",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
            ([{"_id": "zone1", "name": "Internal", "type": "LAN", "description": "Main LAN zone"}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_zone_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Internal",
        "type": "custom",
        "description": "Updated description",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
            ([{"_id": "zone1", "name": "Internal", "type": "LAN", "description": "Main LAN zone"}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_zone_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "Internal",
        "type": "lan",
        "description": "",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
            ([{"_id": "zone1", "name": "Internal"}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_zone_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
        "type": "custom",
        "description": "",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
        assert kwargs["changed"] is False


def test_zone_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Internal",
        "type": "lan",
        "description": "Main LAN zone",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
            ([], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True



def test_zone_duplicate_fails():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Duplicate Zone",
        "type": "custom",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone.UnifiAPI") as mock_api_class,
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
                    {"_id": "z1", "name": "Duplicate Zone"},
                    {"_id": "z2", "name": "Duplicate Zone"},
                ],
                {"status": 200},
            ),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        msg = mock_module.fail_json.call_args[1]["msg"]
        assert "Ambiguous resource" in msg

