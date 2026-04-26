from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy import run_module


def test_firewall_policy_create():
    # 1. Setup Mock Module Params
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Test Policy",
        "action": "ALLOW",
        "protocol": "all",
        "index": 10000,
        "enabled": True,
        "logging": False,
        "source": {"zone": "Internal"},
        "destination": {"zone": "Internal"},
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.UnifiAPI") as mock_api_class,
    ):
        # Configure Mock Module
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        # Configure Mock API
        mock_api = mock_api_class.return_value

        # Mock Zones
        mock_api.request.side_effect = [
            # First call: Get zones
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            # Second call: Get existing policies
            ([], {"status": 200}),
            # Third call: Create policy (POST)
            ({"name": "Test Policy", "_id": "new123"}, {"status": 201}),
        ]

        # 2. Run Module
        run_module()

        # 3. Assertions
        mock_api.login.assert_called_once()

        # Verify POST was called
        # The third call to request should be the POST
        # request(path, method='POST', data=...)
        # Note: request is called 3 times total in this scenario
        assert mock_api.request.call_count == 3

        last_call_args = mock_api.request.call_args_list[2]
        assert last_call_args[1]["method"] == "POST"
        assert last_call_args[1]["data"]["name"] == "Test Policy"

        # Verify exit_json was called
        mock_module.exit_json.assert_called_once()
        args, kwargs = mock_module.exit_json.call_args
        assert kwargs["changed"] is True
        assert kwargs["policy"]["_id"] == "new123"


def test_firewall_policy_absent():
    params = {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "Existing Policy",
        "action": "ALLOW",
        "protocol": "all",
        "index": 10000,
        "enabled": True,
        "logging": False,
        "source": {"zone": "Internal"},
        "destination": {"zone": "Internal"},
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_api = mock_api_class.return_value

        # Mock responses
        mock_api.request.side_effect = [
            # Get zones
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            # Get existing policies (find the one to delete)
            (
                [
                    {
                        "name": "Existing Policy",
                        "_id": "old123",
                        "source": {"zone_id": "zone123"},
                        "destination": {"zone_id": "zone123"},
                    }
                ],
                {"status": 200},
            ),
            # Delete policy
            (None, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 3
        last_call_args = mock_api.request.call_args_list[2]
        assert last_call_args[1]["method"] == "DELETE"
        assert "old123" in last_call_args[0][0]

        mock_module.exit_json.assert_called_once_with(changed=True, policy=None)
