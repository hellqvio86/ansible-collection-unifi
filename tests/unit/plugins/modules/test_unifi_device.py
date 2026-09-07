from unittest.mock import patch

import pytest

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device import run_module


def test_device_missing_identifiers():
    with patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = {
            "state": "present",
            "mac": None,
            "name": None,
            "id": None,
        }
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "At least one of 'mac', 'name', or 'id'" in mock_module.fail_json.call_args[1]["msg"]


def test_device_invalid_mac():
    with patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = {
            "state": "present",
            "mac": "invalid-mac",
            "name": None,
            "id": None,
        }
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "Invalid MAC address" in mock_module.fail_json.call_args[1]["msg"]


def test_device_invalid_brightness():
    with patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = {
            "state": "present",
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": None,
            "id": None,
            "led_override_color_brightness": 150,
        }
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "must be between 1 and 100" in mock_module.fail_json.call_args[1]["msg"]


def test_device_not_found_on_present():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": None,
        "id": None,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = []
        mock_api.request.return_value = ([], {"status": 200})

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "not found on controller" in mock_module.fail_json.call_args[1]["msg"]


def test_device_absent_when_not_found():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": None,
        "id": None,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = []
        mock_api.request.return_value = ([], {"status": 200})

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert "not registered" in kwargs["msg"]


def test_device_absent_delete_success():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": None,
        "id": None,
    }

    existing_device = {
        "_id": "dev123",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "AP-Hallway",
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = [existing_device]
        mock_api.request.side_effect = [
            ([existing_device], {"status": 200}),  # stat/device
            ({}, {"status": 200}),  # DELETE /rest/device/dev123
        ]

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert mock_api.request.call_count == 2
        call_url = mock_api.request.call_args_list[1][0][0]
        assert "/rest/device/dev123" in call_url


def test_device_present_adopt_pending():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "adopt": True,
    }

    existing_device = {
        "_id": "dev123",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "New-AP",
        "adopted": False,
        "state": 2,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = [existing_device]
        mock_api.request.side_effect = [
            ([existing_device], {"status": 200}),  # stat/device
            ({"data": []}, {"status": 200}),       # cmd/devmgr adopt
        ]

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert mock_api.request.call_count == 2
        adopt_call = mock_api.request.call_args_list[1]
        assert "/cmd/devmgr" in adopt_call[0][0]
        assert adopt_call[1]["data"]["cmd"] == "adopt"


def test_device_present_update_attributes():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office-AP",
        "led_override": "off",
        "note": "Office ceiling mount",
        "disabled": False,
    }

    existing_device = {
        "_id": "dev123",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Old-AP-Name",
        "adopted": True,
        "state": 1,
        "led_override": "default",
        "disabled": False,
        "note": "",
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = [existing_device]
        mock_api.request.side_effect = [
            ([existing_device], {"status": 200}),  # stat/device
            (
                {
                    "data": [
                        {
                            **existing_device,
                            "name": "Office-AP",
                            "led_override": "off",
                            "note": "Office ceiling mount",
                        }
                    ]
                },
                {"status": 200},
            ),  # PUT
        ]

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["diff"]["before"]["name"] == "Old-AP-Name"
        assert kwargs["diff"]["after"]["name"] == "Office-AP"
        assert kwargs["diff"]["before"]["led_override"] == "default"
        assert kwargs["diff"]["after"]["led_override"] == "off"
        assert kwargs["device"]["name"] == "Office-AP"


def test_device_present_idempotent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office-AP",
        "led_override": "off",
        "note": "Office ceiling mount",
        "disabled": False,
    }

    existing_device = {
        "_id": "dev123",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office-AP",
        "adopted": True,
        "state": 1,
        "led_override": "off",
        "disabled": False,
        "note": "Office ceiling mount",
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = [existing_device]
        mock_api.request.return_value = ([existing_device], {"status": 200})

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert mock_api.request.call_count == 1


def test_device_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office-AP-New",
    }

    existing_device = {
        "_id": "dev123",
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office-AP-Old",
        "adopted": True,
        "state": 1,
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True

        mock_api = mock_api_class.return_value
        mock_api.as_list.return_value = [existing_device]
        mock_api.request.return_value = ([existing_device], {"status": 200})

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["diff"]["before"]["name"] == "Office-AP-Old"
        assert kwargs["diff"]["after"]["name"] == "Office-AP-New"
        # In check mode, no PUT request should have been made
        assert mock_api.request.call_count == 1
