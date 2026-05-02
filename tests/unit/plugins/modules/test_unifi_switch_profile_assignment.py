from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment import run_module


def test_switch_profile_assignment():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "switch_name": "Switch-01",
        "switch_mac": None,
        "switch_ip": None,
        "profile_name": "Access Switch Profile",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch switch profiles
            ([{"name": "Access Switch Profile", "_id": "switch_prof123"}], {"status": 200}),
            # 2. Fetch devices
            (
                [
                    {
                        "name": "Switch-01",
                        "type": "usw",
                        "_id": "device123",
                        "mac": "00:11:22:33:44:55",
                        "ip": "192.168.1.10",
                    }
                ],
                {"status": 200},
            ),
            # 3. Update device (PUT)
            (
                {
                    "name": "Switch-01",
                    "type": "usw",
                    "_id": "device123",
                    "switch_profile_id": "switch_prof123",
                },
                {"status": 200},
            ),
        ]

        run_module()

        # Verify PUT call
        assert mock_api.request.call_count == 3
        last_call = mock_api.request.call_args_list[2]
        assert last_call[1]["method"] == "PUT"
        assert last_call[1]["data"]["switch_profile_id"] == "switch_prof123"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["switch"]["switch_profile_id"] == "switch_prof123"


def test_switch_profile_assignment_no_change():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "switch_name": None,
        "switch_mac": "00:11:22:33:44:55",
        "switch_ip": None,
        "profile_name": "Access Switch Profile",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch switch profiles
            ([{"name": "Access Switch Profile", "_id": "switch_prof123"}], {"status": 200}),
            # 2. Fetch devices (already has the profile assigned)
            (
                [
                    {
                        "name": "Switch-01",
                        "type": "usw",
                        "_id": "device123",
                        "mac": "00:11:22:33:44:55",
                        "switch_profile_id": "switch_prof123",
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        # Verify no PUT call
        assert mock_api.request.call_count == 2

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_switch_profile_assignment_remove():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "switch_name": None,
        "switch_mac": None,
        "switch_ip": "192.168.1.10",
        "profile_name": "Access Switch Profile",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch switch profiles
            ([{"name": "Access Switch Profile", "_id": "switch_prof123"}], {"status": 200}),
            # 2. Fetch devices
            (
                [
                    {
                        "name": "Switch-01",
                        "type": "usw",
                        "_id": "device123",
                        "ip": "192.168.1.10",
                        "switch_profile_id": "switch_prof123",
                    }
                ],
                {"status": 200},
            ),
            # 3. Update device (PUT) to remove profile
            (
                {
                    "name": "Switch-01",
                    "type": "usw",
                    "_id": "device123",
                    "switch_profile_id": None,
                },
                {"status": 200},
            ),
        ]

        run_module()

        # Verify PUT call with None
        assert mock_api.request.call_count == 3
        last_call = mock_api.request.call_args_list[2]
        assert last_call[1]["method"] == "PUT"
        assert last_call[1]["data"]["switch_profile_id"] is None

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True