from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile import run_module


def test_switch_profile_create():
    params = {
        "host": "192.168.1.1",
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

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch port profiles
            ([{"name": "WAN-Profile", "_id": "port1"}, {"name": "IoT-Profile", "_id": "port2"}], {"status": 200}),
            # 2. Fetch existing switch profiles
            ([], {"status": 200}),
            # 3. Create profile (POST)
            ({"name": "Access Switch Profile", "_id": "switch_prof123"}, {"status": 201}),
        ]

        run_module()

        # Verify POST call
        assert mock_api.request.call_count == 3
        last_call = mock_api.request.call_args_list[2]
        assert last_call[1]["method"] == "POST"
        assert last_call[1]["data"]["name"] == "Access Switch Profile"
        assert last_call[1]["data"]["model"] == "USW-Flex"
        assert last_call[1]["data"]["port_overrides"] == {1: "port1", 2: "port2"}

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["profile"]["_id"] == "switch_prof123"


def test_switch_profile_no_change():
    params = {
        "host": "192.168.1.1",
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

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch port profiles
            ([{"name": "WAN-Profile", "_id": "port1"}], {"status": 200}),
            # 2. Fetch existing profiles (matches desired)
            (
                [
                    {
                        "name": "Existing Profile",
                        "_id": "switch_prof123",
                        "model": "USW-Flex",
                        "port_overrides": {1: "port1"},
                        "description": "Existing profile",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        # Verify no POST/PUT call
        assert mock_api.request.call_count == 2

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert kwargs["profile"]["_id"] == "switch_prof123"