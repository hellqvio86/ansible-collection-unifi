from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment import run_module


def test_switch_profile_assignment():
    params = {
        "host": "192.0.2.1",
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
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI"
        ) as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")
        mock_module.fail_json.side_effect = Exception("fail_json called")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

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
                        "ip": "192.0.2.10",
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
        assert kwargs["results"][0]["switch"]["switch_profile_id"] == "switch_prof123"


def test_switch_profile_assignment_no_change():
    params = {
        "host": "192.0.2.1",
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
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI"
        ) as mock_api_class,
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
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "switch_name": None,
        "switch_mac": None,
        "switch_ip": "192.0.2.10",
        "profile_name": "Access Switch Profile",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI"
        ) as mock_api_class,
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
                        "ip": "192.0.2.10",
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


def test_switch_profile_assignment_fallback():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "switch_name": "Switch-01",
        "profile_name": "Access Switch Profile",
        "switch_profiles": [
            {
                "name": "Access Switch Profile",
                "port_profile_overrides": {
                    "1": "WAN-Profile",
                    "12": "Trunk-Profile",
                    "2": "IoT-Profile",
                },
            }
        ],
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment.UnifiAPI"
        ) as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json called")
        mock_module.exit_json.side_effect = SystemExit("exit_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            # 1. Fetch switch profiles (failed/unsupported)
            (None, {"status": 404}),
            # 2. Fetch portconf
            (
                [
                    {"name": "WAN-Profile", "_id": "wan_id"},
                    {"name": "Trunk-Profile", "_id": "trunk_id"},
                    {"name": "IoT-Profile", "_id": "iot_id"},
                ],
                {"status": 200},
            ),
            # 3. Fetch devices
            (
                [
                    {
                        "name": "Switch-01",
                        "type": "usw",
                        "_id": "device123",
                        "mac": "00:11:22:33:44:55",
                        "ip": "192.0.2.10",
                        "port_overrides": [
                            # Port 1 has some old setup
                            {"port_idx": 1, "portconf_id": "old_wan_id", "setting_preference": "auto"},
                            # Port 2 has some old setup
                            {
                                "port_idx": 2,
                                "portconf_id": "old_iot_id",
                                "poe_mode": "off",
                                "setting_preference": "manual",
                            },
                        ],
                    }
                ],
                {"status": 200},
            ),
            # 4. PUT device
            (
                {
                    "name": "Switch-01",
                    "type": "usw",
                    "_id": "device123",
                },
                {"status": 200},
            ),
        ]

        try:
            run_module()
        except SystemExit:
            pass

        # Verify calls
        assert mock_api.request.call_count == 4

        # Verify PUT data
        put_call = mock_api.request.call_args_list[3]
        assert put_call[1]["method"] == "PUT"

        overrides = put_call[1]["data"]["port_overrides"]
        assert len(overrides) == 3

        # Find individual overrides to inspect
        p1 = next(o for o in overrides if o["port_idx"] == 1)
        p2 = next(o for o in overrides if o["port_idx"] == 2)
        p12 = next(o for o in overrides if o["port_idx"] == 12)

        # Port 1 should have poe_mode: auto and setting_preference: manual, and profile: wan_id
        assert p1["portconf_id"] == "wan_id"
        assert p1["poe_mode"] == "auto"
        assert p1["setting_preference"] == "manual"

        # Port 2 should have its original poe_mode: off, setting_preference: manual, and profile: iot_id
        assert p2["portconf_id"] == "iot_id"
        assert p2["poe_mode"] == "off"
        assert p2["setting_preference"] == "manual"

        # Port 12 (new override) should have poe_mode: auto, setting_preference: manual, and profile: trunk_id
        assert p12["portconf_id"] == "trunk_id"
        assert p12["poe_mode"] == "auto"
        assert p12["setting_preference"] == "manual"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
