from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_nat_rule import run_module

# Shared networkconf response — network name → _id resolution
_NETCONF_DATA = [{"_id": "net-iot-1", "name": "LAN_IoT"}]
_NETCONF_RESP = (_NETCONF_DATA, {"status": 200})

_MODULE = "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_nat_rule"


def _setup_mocks(mock_module_class, mock_api_class, params, request_side_effects):
    mock_module = mock_module_class.return_value
    mock_module.params = params
    mock_module.check_mode = False
    mock_module.fail_json.side_effect = Exception("fail_json called")

    mock_api = mock_api_class.return_value
    mock_api.as_list.side_effect = lambda x: (
        x if isinstance(x, list)
        else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
    )
    mock_api.request.side_effect = request_side_effects
    return mock_module, mock_api


def _base_params(**overrides):
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "unifi_session_cookie": None,
        "unifi_csrf_token": None,
        "state": "present",
        "name": "SNAT HA to IoT",
        "type": "masquerade",
        "src_address": "192.0.2.10",
        "dst_address": "198.51.100.0/24",
        "outbound_interface": "LAN_IoT",
        "translated_src": "",
        "enabled": True,
        "logging": False,
    }
    params.update(overrides)
    return params


def test_nat_rule_create():
    """Creating a rule that does not yet exist should POST and report changed=True."""
    created_rule = {
        "_id": "nat-1",
        "name": "SNAT HA to IoT",
        "type": "masquerade",
        "src_address": "192.0.2.10",
        "dst_address": "198.51.100.0/24",
        "outbound_network_id": "net-iot-1",
        "enabled": True,
        "logging": False,
    }

    with (
        patch(f"{_MODULE}.AnsibleModule") as mock_module_class,
        patch(f"{_MODULE}.UnifiAPI") as mock_api_class,
    ):
        mock_module, mock_api = _setup_mocks(
            mock_module_class, mock_api_class,
            _base_params(),
            [
                _NETCONF_RESP,                          # _resolve_network_id (outbound_interface set)
                ([], {"status": 200}),                  # GET nat rules → empty
                ([created_rule], {"status": 201}),      # POST → created
            ],
        )

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["rule"]["_id"] == "nat-1"

        post_call = mock_api.request.call_args_list[2]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "SNAT HA to IoT"
        assert post_call[1]["data"]["outbound_network_id"] == "net-iot-1"


def test_nat_rule_no_change():
    """If the rule already matches desired state, exit with changed=False."""
    existing_rule = {
        "_id": "nat-1",
        "name": "SNAT HA to IoT",
        "type": "masquerade",
        "src_address": "192.0.2.10",
        "dst_address": "198.51.100.0/24",
        "outbound_network_id": "net-iot-1",
        "enabled": True,
        "logging": False,
    }

    with (
        patch(f"{_MODULE}.AnsibleModule") as mock_module_class,
        patch(f"{_MODULE}.UnifiAPI") as mock_api_class,
    ):
        mock_module, _ = _setup_mocks(
            mock_module_class, mock_api_class,
            _base_params(),
            [
                _NETCONF_RESP,                          # _resolve_network_id
                ([existing_rule], {"status": 200}),     # GET → rule exists and matches
            ],
        )

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_nat_rule_update():
    """If the rule exists but differs, it should PUT and report changed=True."""
    existing_rule = {
        "_id": "nat-1",
        "name": "SNAT HA to IoT",
        "type": "masquerade",
        "src_address": "192.0.2.10",
        "dst_address": "198.51.100.0/24",
        "outbound_network_id": "net-iot-1",
        "enabled": False,   # will be toggled to True
        "logging": False,
    }
    updated_rule = {**existing_rule, "enabled": True}

    with (
        patch(f"{_MODULE}.AnsibleModule") as mock_module_class,
        patch(f"{_MODULE}.UnifiAPI") as mock_api_class,
    ):
        mock_module, mock_api = _setup_mocks(
            mock_module_class, mock_api_class,
            _base_params(enabled=True),
            [
                _NETCONF_RESP,                          # _resolve_network_id
                ([existing_rule], {"status": 200}),     # GET → rule differs
                ([updated_rule], {"status": 200}),      # PUT → updated
            ],
        )

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True

        put_call = mock_api.request.call_args_list[2]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["enabled"] is True


def test_nat_rule_delete():
    """state=absent on an existing rule should DELETE and report changed=True.

    outbound_interface="" so _resolve_network_id returns early without an API call.
    """
    existing_rule = {
        "_id": "nat-1",
        "name": "SNAT HA to IoT",
        "type": "masquerade",
        "src_address": "192.0.2.10",
        "dst_address": "198.51.100.0/24",
        "enabled": True,
        "logging": False,
    }

    with (
        patch(f"{_MODULE}.AnsibleModule") as mock_module_class,
        patch(f"{_MODULE}.UnifiAPI") as mock_api_class,
    ):
        mock_module, mock_api = _setup_mocks(
            mock_module_class, mock_api_class,
            _base_params(state="absent", outbound_interface=""),
            [
                # no netconf call — outbound_interface is empty
                ([existing_rule], {"status": 200}),     # GET → rule found
                ({}, {"status": 204}),                  # DELETE
            ],
        )

        run_module()

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["rule"] is None

        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"
        assert "nat-1" in delete_call[0][0]


def test_nat_rule_absent_already_gone():
    """state=absent on a non-existent rule should be a no-op (changed=False)."""
    with (
        patch(f"{_MODULE}.AnsibleModule") as mock_module_class,
        patch(f"{_MODULE}.UnifiAPI") as mock_api_class,
    ):
        mock_module, _ = _setup_mocks(
            mock_module_class, mock_api_class,
            _base_params(state="absent", outbound_interface=""),
            [
                # no netconf call — outbound_interface is empty
                ([], {"status": 200}),                  # GET → empty list
            ],
        )

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert kwargs["rule"] is None
