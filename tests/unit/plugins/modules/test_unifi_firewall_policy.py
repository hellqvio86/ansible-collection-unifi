from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy import run_module


def test_firewall_policy_create():
    # 1. Setup Mock Module Params
    params = {
        "host": "192.0.2.1",
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
        "policies": None,
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
        mock_module.fail_json.side_effect = Exception("fail_json")

        # Configure Mock API
        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        # Mock Zones, Networks, and Policies
        mock_api.request.side_effect = [
            # First call: Get zones
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            # Second call: Get networks
            ([], {"status": 200}),
            # Third call: Get existing policies
            ([], {"status": 200}),
            # Fourth call: Create policy (POST)
            ({"name": "Test Policy", "_id": "new123"}, {"status": 201}),
        ]

        # 2. Run Module
        run_module()

        # 3. Assertions
        mock_api.login.assert_called_once()

        # Verify POST was called
        # Note: request is called 4 times total in this scenario
        assert mock_api.request.call_count == 4

        last_call_args = mock_api.request.call_args_list[3]
        assert last_call_args[1]["method"] == "POST"
        assert last_call_args[1]["data"]["name"] == "Test Policy"

        # Verify exit_json was called
        mock_module.exit_json.assert_called_once()
        args, kwargs = mock_module.exit_json.call_args
        assert kwargs["changed"] is True
        assert kwargs["policy"]["_id"] == "new123"


def test_firewall_policy_absent():
    params = {
        "host": "192.0.2.1",
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
        "policies": None,
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
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])

        # Mock responses
        mock_api.request.side_effect = [
            # Get zones
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            # Get networks
            ([], {"status": 200}),
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

        assert mock_api.request.call_count == 4
        last_call_args = mock_api.request.call_args_list[3]
        assert last_call_args[1]["method"] == "DELETE"
        assert "old123" in last_call_args[0][0]

        mock_module.exit_json.assert_called_once_with(changed=True, policies=[None], policy=None)
