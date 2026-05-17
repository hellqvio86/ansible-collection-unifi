from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group import run_module


def test_firewall_group_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Web Ports",
        "group_type": "port-group",
        "group_members": ["80", "443"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([], {"status": 200}),
            ([{"_id": "grp1", "name": "Web Ports", "group_type": "port-group", "group_members": ["80", "443"]}], {"status": 201}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["group_members"] == ["80", "443"]

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_firewall_group_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Web Ports",
        "group_type": "port-group",
        "group_members": ["80", "443"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"_id": "grp1", "name": "Web Ports", "group_type": "port-group", "group_members": ["80", "443"]}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_firewall_group_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Web Ports",
        "group_type": "port-group",
        "group_members": ["80", "443", "8080"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"_id": "grp1", "name": "Web Ports", "group_type": "port-group", "group_members": ["80", "443"]}], {"status": 200}),
            ([{"_id": "grp1", "name": "Web Ports", "group_type": "port-group", "group_members": ["80", "443", "8080"]}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["group_members"] == ["80", "443", "8080"]

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_firewall_group_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "Web Ports",
        "group_type": "address-group",
        "group_members": None,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"_id": "grp1", "name": "Web Ports"}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_firewall_group_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
        "group_type": "address-group",
        "group_members": None,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_firewall_group_type_mismatch():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Web Ports",
        "group_type": "address-group",
        "group_members": ["192.168.1.0/24"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"_id": "grp1", "name": "Web Ports", "group_type": "port-group"}], {"status": 200}),
        ]

        import pytest
        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "different type" in args["msg"].lower()


def test_firewall_group_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Web Ports",
        "group_type": "port-group",
        "group_members": ["80", "443"],
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
