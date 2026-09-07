# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_network import (
    _build_desired_payload,
    run_module,
)


class AnsibleExitJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs
        super().__init__("AnsibleExitJson")


class AnsibleFailJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs
        super().__init__(kwargs.get("msg", "AnsibleFailJson"))


def test_build_desired_payload_corporate() -> None:
    params = {
        "name": "IoT VLAN",
        "purpose": "corporate",
        "vlan": 20,
        "ip_subnet": "192.168.20.1/24",
        "dhcpd_enabled": True,
        "dhcp_start": "192.168.20.10",
        "dhcp_stop": "192.168.20.200",
        "dhcp_lease_time": 86400,
        "dhcp_dns_1": "1.1.1.1",
        "dhcp_dns_2": "8.8.8.8",
        "dhcp_guarding": True,
        "dhcp_guarding_servers": ["192.168.20.1"],
        "igmp_snooping": True,
        "multicast_dns": True,
        "domain_name": "iot.local",
    }
    payload = _build_desired_payload(params)
    assert payload["name"] == "IoT VLAN"
    assert payload["purpose"] == "corporate"
    assert payload["vlan"] == "20"
    assert payload["vlan_enabled"] is True
    assert payload["ip_subnet"] == "192.168.20.1/24"
    assert payload["dhcpd_enabled"] is True
    assert payload["dhcpd_start"] == "192.168.20.10"
    assert payload["dhcpd_stop"] == "192.168.20.200"
    assert payload["dhcpd_leasetime"] == 86400
    assert payload["dhcpd_dns_1"] == "1.1.1.1"
    assert payload["dhcpd_dns_2"] == "8.8.8.8"
    assert payload["dhcpd_dns_enabled"] is True
    assert payload["dhcp_guard_enabled"] is True
    assert payload["dhcp_guard_servers"] == ["192.168.20.1"]
    assert payload["igmp_snooping"] is True
    assert payload["mdns_enabled"] is True
    assert payload["domain_name"] == "iot.local"


def test_build_desired_payload_vlan_only() -> None:
    params = {
        "name": "CCTV VLAN",
        "purpose": "vlan-only",
        "vlan": 50,
    }
    payload = _build_desired_payload(params)
    assert payload["name"] == "CCTV VLAN"
    assert payload["purpose"] == "vlan-only"
    assert payload["vlan"] == "50"
    assert payload["vlan_enabled"] is True
    assert "ip_subnet" not in payload


def _run_mock_module(params: dict[str, Any], api_mock: MagicMock, check_mode: bool = False) -> dict[str, Any]:
    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_network.AnsibleModule") as mock_mod_cls,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_network.UnifiAPI") as mock_api_cls,
    ):
        mock_module = MagicMock()
        mock_module.check_mode = check_mode
        mock_module._diff = False

        result: dict[str, Any] = {}

        def exit_json(**kwargs: Any) -> None:
            result.update(kwargs)
            raise AnsibleExitJson(kwargs)

        def fail_json(**kwargs: Any) -> None:
            result.update(kwargs)
            raise AnsibleFailJson(kwargs)

        mock_module.exit_json.side_effect = exit_json
        mock_module.fail_json.side_effect = fail_json

        def mock_init(argument_spec: dict[str, Any], **kwargs: Any) -> MagicMock:
            merged = {}
            for k, v in argument_spec.items():
                if "default" in v:
                    merged[k] = v["default"]
                else:
                    merged[k] = None
            merged.update(params)
            mock_module.params = merged
            mock_module.argument_spec = argument_spec
            return mock_module

        mock_mod_cls.side_effect = mock_init
        mock_api_cls.return_value = api_mock

        try:
            run_module()
        except AnsibleExitJson:
            pass

        return result


def test_create_corporate_network() -> None:
    params = {
        "name": "New-VLAN-10",
        "purpose": "corporate",
        "vlan": 10,
        "ip_subnet": "192.168.10.1/24",
        "state": "present",
    }
    api_mock = MagicMock()
    api_mock.as_list.side_effect = lambda x: (
        x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) else [])
    )
    api_mock.request.side_effect = [
        ([], {"status": 200}),  # existing networks GET
        ([{"_id": "net_new_10", "name": "New-VLAN-10", "vlan": "10"}], {"status": 201}),  # POST
    ]

    res = _run_mock_module(params, api_mock)
    assert res.get("changed") is True
    assert api_mock.request.call_count == 2
    post_call = api_mock.request.call_args_list[1]
    assert post_call[1]["method"] == "POST"


def test_idempotent_network() -> None:
    existing_item = {
        "_id": "net_10",
        "name": "New-VLAN-10",
        "purpose": "corporate",
        "vlan": "10",
        "vlan_enabled": True,
        "ip_subnet": "192.168.10.1/24",
        "enabled": True,
        "networkgroup": "LAN",
    }
    params = {
        "name": "New-VLAN-10",
        "purpose": "corporate",
        "vlan": 10,
        "ip_subnet": "192.168.10.1/24",
        "state": "present",
    }
    api_mock = MagicMock()
    api_mock.as_list.side_effect = lambda x: (
        x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) else [])
    )
    api_mock.request.return_value = ([existing_item], {"status": 200})

    res = _run_mock_module(params, api_mock)
    assert res.get("changed") is False
    assert api_mock.request.call_count == 1


def test_update_network() -> None:
    existing_item = {
        "_id": "net_10",
        "name": "New-VLAN-10",
        "purpose": "corporate",
        "vlan": "10",
        "vlan_enabled": True,
        "ip_subnet": "192.168.10.1/24",
        "enabled": True,
        "networkgroup": "LAN",
    }
    params = {
        "name": "New-VLAN-10",
        "purpose": "corporate",
        "vlan": 10,
        "ip_subnet": "192.168.10.1/24",
        "dhcp_start": "192.168.10.50",
        "state": "present",
    }
    api_mock = MagicMock()
    api_mock.as_list.side_effect = lambda x: (
        x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) else [])
    )
    api_mock.request.side_effect = [
        ([existing_item], {"status": 200}),  # GET
        ([dict(existing_item, dhcpd_start="192.168.10.50")], {"status": 200}),  # PUT
    ]

    res = _run_mock_module(params, api_mock)
    assert res.get("changed") is True
    assert api_mock.request.call_count == 2
    put_call = api_mock.request.call_args_list[1]
    assert put_call[1]["method"] == "PUT"


def test_delete_network() -> None:
    existing_item = {
        "_id": "net_10",
        "name": "Old-VLAN",
        "purpose": "corporate",
    }
    params = {
        "name": "Old-VLAN",
        "state": "absent",
    }
    api_mock = MagicMock()
    api_mock.as_list.side_effect = lambda x: (
        x if isinstance(x, list) else (x.get("data", []) if isinstance(x, dict) else [])
    )
    api_mock.request.side_effect = [
        ([existing_item], {"status": 200}),  # GET
        ([], {"status": 200}),  # DELETE
    ]

    res = _run_mock_module(params, api_mock)
    assert res.get("changed") is True
    del_call = api_mock.request.call_args_list[1]
    assert del_call[1]["method"] == "DELETE"


def test_cannot_delete_default_network() -> None:
    existing_default = {
        "_id": "net_default",
        "name": "Default",
        "default": True,
    }
    params = {
        "name": "Default",
        "state": "absent",
    }
    api_mock = MagicMock()
    api_mock.as_list.return_value = [existing_default]
    api_mock.request.return_value = ([existing_default], {"status": 200})

    with pytest.raises(AnsibleFailJson) as exc_info:
        _run_mock_module(params, api_mock)
    assert "cannot delete default" in str(exc_info.value).lower()


def test_invalid_vlan_range() -> None:
    params = {
        "name": "Bad-VLAN",
        "purpose": "vlan-only",
        "vlan": 5000,
        "state": "present",
    }
    api_mock = MagicMock()
    with pytest.raises(AnsibleFailJson) as exc_info:
        _run_mock_module(params, api_mock)
    assert "between 1 and 4094" in str(exc_info.value)
