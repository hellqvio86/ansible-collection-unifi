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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

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


def test_firewall_policy_create_icmp():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Allow ICMP",
        "action": "ALLOW",
        "protocol": "icmp",
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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            ([], {"status": 200}),
            ([], {"status": 200}),
            ({"name": "Allow ICMP", "_id": "new123"}, {"status": 201}),
        ]

        run_module()

        assert mock_api.request.call_count == 4
        last_call_args = mock_api.request.call_args_list[3]
        assert last_call_args[1]["method"] == "POST"
        assert last_call_args[1]["data"]["protocol"] == "icmp"
        assert last_call_args[1]["data"]["ip_version"] == "IPV4"

        mock_module.exit_json.assert_called_once()
        args, kwargs = mock_module.exit_json.call_args
        assert kwargs["changed"] is True


def test_firewall_policy_ambiguous_match_fails():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Duplicate Policy",
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
        mock_module.fail_json.side_effect = Exception("fail_json called")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            ([], {"status": 200}),
            (
                [
                    {
                        "name": "Duplicate Policy",
                        "_id": "dup1",
                        "source": {"zone_id": "zone123"},
                        "destination": {"zone_id": "zone123"},
                    },
                    {
                        "name": "Duplicate Policy",
                        "_id": "dup2",
                        "source": {"zone_id": "zone123"},
                        "destination": {"zone_id": "zone123"},
                    },
                ],
                {"status": 200},
            ),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args, kwargs = mock_module.fail_json.call_args
        assert "ambiguous" in kwargs["msg"].lower()


def test_firewall_policy_missing_name_fails_fast():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "name": None,
        "policies": None,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy.UnifiAPI"),
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json called")

        import pytest

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        mock_module.fail_json.assert_called_once_with(msg="Either name or policies is required")


def test_firewall_policy_drift_update_extended_fields():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "ICMP Policy",
        "action": "ALLOW",
        "protocol": "icmp",
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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        existing_policy = {
            "name": "ICMP Policy",
            "_id": "pol1",
            "action": "ALLOW",
            "protocol": "icmp",
            "ip_version": "IPV4",
            "index": 10000,
            "enabled": True,
            "logging": False,
            "schedule": {"mode": "ALWAYS"},
            "connection_state_type": "ALL",
            "connection_states": [],
            "create_allow_respond": True,
            "icmp_typename": "ECHO_REQUEST",  # Differs from ANY
            "icmp_v6_typename": "ANY",
            "match_ip_sec": False,
            "match_opposite_protocol": False,
            "source": {
                "zone_id": "zone123",
                "matching_target": "ANY",
                "match_opposite_ports": False,
                "port_matching_type": "ANY",
            },
            "destination": {
                "zone_id": "zone123",
                "matching_target": "ANY",
                "match_opposite_ports": False,
                "port_matching_type": "ANY",
            },
        }

        mock_api.request.side_effect = [
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            ([], {"status": 200}),
            ([existing_policy], {"status": 200}),
            ({"name": "ICMP Policy", "_id": "pol1"}, {"status": 200}),  # PUT
        ]

        run_module()

        # Check that PUT was called because icmp_typename drifted
        assert mock_api.request.call_count == 4
        put_call = mock_api.request.call_args_list[3]
        assert put_call[1]["method"] == "PUT"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_firewall_policy_drift_update_match_opposite_ports():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Port Policy",
        "action": "ALLOW",
        "protocol": "tcp",
        "index": 10000,
        "enabled": True,
        "logging": False,
        "source": {"zone": "Internal", "port": "8080", "match_opposite_ports": True},
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
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        existing_policy = {
            "name": "Port Policy",
            "_id": "pol2",
            "action": "ALLOW",
            "protocol": "tcp",
            "ip_version": "BOTH",
            "index": 10000,
            "enabled": True,
            "logging": False,
            "schedule": {"mode": "ALWAYS"},
            "connection_state_type": "ALL",
            "connection_states": [],
            "create_allow_respond": True,
            "icmp_typename": "ANY",
            "icmp_v6_typename": "ANY",
            "match_ip_sec": False,
            "match_opposite_protocol": False,
            "source": {
                "zone_id": "zone123",
                "matching_target": "ANY",
                "match_opposite_ports": False,  # Differs from True
                "port_matching_type": "SPECIFIC",
                "port": "8080",
            },
            "destination": {
                "zone_id": "zone123",
                "matching_target": "ANY",
                "match_opposite_ports": False,
                "port_matching_type": "ANY",
            },
        }

        mock_api.request.side_effect = [
            ([{"name": "Internal", "_id": "zone123"}], {"status": 200}),
            ([], {"status": 200}),
            ([existing_policy], {"status": 200}),
            ({"name": "Port Policy", "_id": "pol2"}, {"status": 200}),  # PUT
        ]

        run_module()

        assert mock_api.request.call_count == 4
        put_call = mock_api.request.call_args_list[3]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["source"]["match_opposite_ports"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True

