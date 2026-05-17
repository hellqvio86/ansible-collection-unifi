from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate import run_module


def test_cert_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----",
        "key": "-----BEGIN PRIVATE KEY-----\nMIIB\n-----END PRIVATE KEY-----",
        "active": True,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([], {"status": 200}),
            ({"id": "cert1", "name": "mycert"}, {"status": 201}),
            ({"id": "cert1", "name": "mycert", "active": True}, {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 3
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "mycert"
        status_call = mock_api.request.call_args_list[2]
        assert status_call[1]["method"] == "PUT"
        assert status_call[1]["data"]["active"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----",
        "key": "-----BEGIN PRIVATE KEY-----\nMIIB\n-----END PRIVATE KEY-----",
        "active": True,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert", "active": True}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_cert_activate_existing():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----",
        "key": "-----BEGIN PRIVATE KEY-----\nMIIB\n-----END PRIVATE KEY-----",
        "active": True,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert", "active": False}], {"status": 200}),
            ({"id": "cert1", "name": "mycert", "active": True}, {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        status_call = mock_api.request.call_args_list[1]
        assert status_call[1]["method"] == "PUT"
        assert status_call[1]["data"]["active"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "mycert",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert"}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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


def test_cert_missing_params():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as _,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        import pytest
        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "cert" in args["msg"].lower() and "key" in args["msg"].lower()


def test_cert_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----",
        "key": "-----BEGIN PRIVATE KEY-----\nMIIB\n-----END PRIVATE KEY-----",
        "active": True,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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
