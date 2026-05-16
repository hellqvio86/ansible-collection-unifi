from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile import run_module


def test_switch_profile_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Access Switch Profile",
        "model": "USW-Flex",
        "port_profile_overrides": {"1": "WAN-Profile", "2": "IoT-Profile"},
        "description": "Standard access switch",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert "managed as logical entities" in kwargs["msg"]


def test_switch_profile_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Existing Profile",
        "model": "USW-Flex",
        "port_profile_overrides": {"1": "WAN-Profile"},
        "description": "Existing profile",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert "managed as logical entities" in kwargs["msg"]
