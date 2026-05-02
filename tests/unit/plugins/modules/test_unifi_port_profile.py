from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile import run_module


def test_port_profile_create():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "IoT Profile",
        "native_network_name": "IoT",
        "tagged_network_names": ["Camera"],
        "poe_mode": "auto",
        "isolation": True,
        "autoneg": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch networks
            ([{"name": "IoT", "_id": "net_iot"}, {"name": "Camera", "_id": "net_cam"}], {"status": 200}),
            # 2. Fetch existing profiles
            ([], {"status": 200}),
            # 3. Create profile (POST)
            ({"name": "IoT Profile", "_id": "prof123"}, {"status": 201}),
        ]

        run_module()

        # Verify POST call
        assert mock_api.request.call_count == 3
        last_call = mock_api.request.call_args_list[2]
        assert last_call[1]["method"] == "POST"
        assert last_call[1]["data"]["native_networkconf_id"] == "net_iot"
        assert last_call[1]["data"]["tagged_networkconf_ids"] == ["net_cam"]

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["profile"]["_id"] == "prof123"


def test_port_profile_no_change():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Existing Profile",
        "native_network_name": "IoT",
        "tagged_network_names": [],
        "poe_mode": "auto",
        "isolation": False,
        "autoneg": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # 1. Fetch networks
            ([{"name": "IoT", "_id": "net_iot"}], {"status": 200}),
            # 2. Fetch existing profiles (matches desired)
            (
                [
                    {
                        "name": "Existing Profile",
                        "_id": "prof123",
                        "native_networkconf_id": "net_iot",
                        "poe_mode": "auto",
                        "isolation": False,
                        "autoneg": True,
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
        assert kwargs["profile"]["_id"] == "prof123"
