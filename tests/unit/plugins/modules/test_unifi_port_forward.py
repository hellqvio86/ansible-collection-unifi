from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward import (
    _build_desired_payload,
    run_module,
)

# ---------------------------------------------------------------------------
# Desired-state builder tests (independent of HTTP/API)
# ---------------------------------------------------------------------------


def test_build_desired_payload_basic():
    params = {
        "enabled": True,
        "protocol": "tcp",
        "fwd_ip": "192.168.1.10",
        "log": False,
        "src": None,
    }
    result = _build_desired_payload("web", params, "80", "8080")
    assert result["name"] == "web"
    assert result["enabled"] is True
    assert result["proto"] == "tcp"
    assert result["dst_port"] == "80"
    assert result["fwd_port"] == "8080"
    assert result["fwd_ip"] == "192.168.1.10"
    assert result["log"] is False
    assert "src" not in result
    assert "fwd_network_id" not in result


def test_build_desired_payload_with_src_and_network():
    params = {
        "enabled": True,
        "protocol": "udp",
        "fwd_ip": "10.0.0.5",
        "log": True,
        "src": "203.0.113.0/24",
    }
    result = _build_desired_payload("vpn", params, "1194", "1194", fwd_network_id="net-abc123")
    assert result["src"] == "203.0.113.0/24"
    assert result["fwd_network_id"] == "net-abc123"
    assert result["log"] is True


def test_build_desired_payload_empty_src_excluded():
    params = {
        "enabled": True,
        "protocol": "tcp",
        "fwd_ip": "192.168.1.1",
        "log": False,
        "src": "",
    }
    result = _build_desired_payload("ssh", params, "22", "22")
    # empty string is falsy, src should not be in payload
    assert "src" not in result


def test_port_forward_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "SSH to Server",
        "enabled": True,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": None,
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
            (
                [
                    {
                        "_id": "pf1",
                        "name": "SSH to Server",
                        "enabled": True,
                        "proto": "tcp",
                        "dst_port": "2222",
                        "fwd_port": "2222",
                        "fwd_ip": "192.168.1.10",
                    }
                ],
                {"status": 201},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "SSH to Server"
        assert post_call[1]["data"]["dst_port"] == "2222"
        assert post_call[1]["data"]["fwd_port"] == "2222"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_port_forward_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "SSH to Server",
        "enabled": True,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": "22",
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
                        "_id": "pf1",
                        "name": "SSH to Server",
                        "enabled": True,
                        "proto": "tcp",
                        "src": "",
                        "dst_port": "2222",
                        "fwd_port": "22",
                        "fwd_ip": "192.168.1.10",
                        "fwd_network_id": "",
                        "log": False,
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


def test_port_forward_update():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "SSH to Server",
        "enabled": False,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": "22",
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
                        "_id": "pf1",
                        "name": "SSH to Server",
                        "enabled": True,
                        "proto": "tcp",
                        "src": "",
                        "dst_port": "2222",
                        "fwd_port": "22",
                        "fwd_ip": "192.168.1.10",
                        "fwd_network_id": "",
                        "log": False,
                    }
                ],
                {"status": 200},
            ),
            (
                [
                    {
                        "_id": "pf1",
                        "name": "SSH to Server",
                        "enabled": False,
                        "proto": "tcp",
                        "src": "",
                        "dst_port": "2222",
                        "fwd_port": "22",
                        "fwd_ip": "192.168.1.10",
                        "fwd_network_id": "",
                        "log": False,
                    }
                ],
                {"status": 200},
            ),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        put_call = mock_api.request.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["data"]["enabled"] is False

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_port_forward_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "SSH to Server",
        "enabled": True,
        "protocol": "tcp_udp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": None,
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
            ([{"_id": "pf1", "name": "SSH to Server", "enabled": True}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert kwargs["rule"] is None


def test_port_forward_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
        "enabled": True,
        "protocol": "tcp_udp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": None,
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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


def test_port_forward_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "SSH to Server",
        "enabled": True,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": None,
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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


def test_port_forward_with_network():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "SSH to Server",
        "enabled": True,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": "22",
        "fwd_ip": "192.168.1.10",
        "fwd_network": "Default",
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
            ([{"_id": "net1", "name": "Default"}], {"status": 200}),
            ([], {"status": 200}),
            ([{"_id": "pf1", "name": "SSH to Server", "enabled": True}], {"status": 201}),
        ]

        run_module()

        assert mock_api.request.call_count == 3
        post_call = mock_api.request.call_args_list[2]
        assert post_call[1]["data"]["fwd_network_id"] == "net1"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_port_forward_ambiguous_fails():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "Duplicate Rule",
        "enabled": True,
        "protocol": "tcp",
        "src": "",
        "dst_port": "2222",
        "fwd_port": "22",
        "fwd_ip": "192.168.1.10",
        "fwd_network": None,
        "log": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward.UnifiAPI") as mock_api_class,
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
            (
                [
                    {"_id": "pf1", "name": "Duplicate Rule"},
                    {"_id": "pf2", "name": "Duplicate Rule"},
                ],
                {"status": 200},
            ),
        ]

        import pytest

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        mock_module.fail_json.assert_called_once()
        kwargs = mock_module.fail_json.call_args[1]
        assert "ambiguous" in kwargs["msg"].lower()
