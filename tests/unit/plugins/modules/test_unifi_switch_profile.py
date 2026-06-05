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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([], {"status": 200}),
            ([{"_id": "prof1", "name": "Access Switch Profile", "model": "USW-Flex"}], {"status": 201}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "Access Switch Profile"
        assert post_call[1]["data"]["model"] == "USW-Flex"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (
                [
                    {
                        "_id": "prof1",
                        "name": "Existing Profile",
                        "model": "USW-Flex",
                        "description": "Existing profile",
                        "port_profile_overrides": {"1": "WAN-Profile"},
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


def test_switch_profile_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Existing Profile",
        "model": "USW-Pro",
        "port_profile_overrides": {"1": "WAN-Profile", "2": "IoT-Profile"},
        "description": "Updated description",
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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (
                [
                    {
                        "_id": "prof1",
                        "name": "Existing Profile",
                        "model": "USW-Flex",
                        "description": "Old description",
                        "port_profile_overrides": {"1": "WAN-Profile"},
                    }
                ],
                {"status": 200},
            ),
            ([{"_id": "prof1", "name": "Existing Profile", "model": "USW-Pro"}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["model"] == "USW-Pro"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_switch_profile_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "Existing Profile",
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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"_id": "prof1", "name": "Existing Profile"}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_switch_profile_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
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


def test_switch_profile_check_mode_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "New Profile",
        "model": "USW-Flex",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.UnifiAPI") as mock_api_class,
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


def test_switch_profile_check_mode_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Existing Profile",
        "model": "USW-Pro",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile.UnifiAPI") as mock_api_class,
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
            ([{"_id": "prof1", "name": "Existing Profile", "model": "USW-Flex"}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_switch_profile_unsupported_api():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Existing Profile",
        "model": "USW-Pro",
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
        mock_module.exit_json.side_effect = SystemExit("exit_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            (None, {"status": 404}),
        ]

        try:
            run_module()
        except SystemExit:
            pass

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert kwargs["switchprofile_api_supported"] is False
        assert "unsupported" in kwargs["msg"]
