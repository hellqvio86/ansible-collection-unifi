# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_device import (
    run_module as run_device,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_reservation import (
    run_module as run_dhcp_reservation,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_dhcp_server import (
    run_module as run_dhcp_server,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_group import (
    run_module as run_firewall_group,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_policy import (
    run_module as run_firewall_policy,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_firewall_zone import (
    run_module as run_firewall_zone,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_info import (
    run_module as run_info,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_login import (
    run_module as run_login,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_nat_rule import (
    run_module as run_nat_rule,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_network import (
    run_module as run_network,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_forward import (
    run_module as run_port_forward,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_port_profile import (
    run_module as run_port_profile,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_rsyslog import (
    run_module as run_rsyslog,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key import (
    run_module as run_ssh_key,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile import (
    run_module as run_switch_profile,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_switch_profile_assignment import (
    run_module as run_switch_profile_assignment,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_system_settings import (
    run_module as run_system_settings,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate import (
    run_module as run_user_certificate,
)
from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_wlan import (
    run_module as run_wlan,
)
from tests.integration.mock_server import MockUniFiServer

TEST_CERT = """-----BEGIN CERTIFICATE-----
MIIBkjCB/KADAgECAgIwOTANBgkqhkiG9w0BAQsFADAPMQ0wCwYDVQQDDAR0ZXN0
MB4XDTI2MDEwMTAwMDAwMFoXDTI3MDEwMTAwMDAwMFowDzENMAsGA1UEAwwEdGVz
dDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA69VsgDxkbzlfifvYKvpjB2q7
+hN+Y/ptQiv8MysViWPDvM7pYabhqCuoqhrXJn9S/ldrxb3hciUCeK3kuUOTnXRa
xJCFjV7P8HbDbAw5pU9UQRwl4/+aLuLvs80DL9NfU8lNmP9GMwmZOzB4DKIKP4ew
BRVWTvA3aavZFGkHfjMCAwEAATANBgkqhkiG9w0BAQsFAAOBgQA5OQ5TA3qLdcye
Ezx81HqRgqFAZZHzrgGM+afYPLkGkmL3ZJVsc5IKv1tceElRVZzg8sXUNysG7ReK
PRMdMtiahVdtPuXskBjPzAB6hbjiIixJVUX052Z9MPUqZoli0ya2kRaSD0z2heNH
yY1NVWKl/hFQw1vrA07wq62GsGJ61g==
-----END CERTIFICATE-----"""

TEST_KEY = """-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAOvVbIA8ZG85X4n7
2Cr6Ywdqu/oTfmP6bUIr/DMrFYljw7zO6WGm4agrqKoa1yZ/Uv5Xa8W94XIlAnit
5LlDk510WsSQhY1ez/B2w2wMOaVPVEEcJeP/mi7i77PNAy/TX1PJTZj/RjMJmTsw
eAyiCj+HsAUVVk7wN2mr2RRpB34zAgMBAAECgYAul9f77fKZ1uf9RviKZTWzfW7u
FXPfJNb5P99v7I8wubkuUGLjnCjxJM8J7IudW4J2JadxRfaIqq82UITj5WoATKMV
aIT4NCbHsGvhoXaeXbK1KgjOlwTtDk80O9udoixIVBKK7/ww3vVYTAdBT/DZtLmd
7pJB25nE52L/RWi1IQJBAPtllkBKHdNIsyuUxqqgOyub2xXQqDPINqV9UOWEZKJo
W3KnRhI8ab8qrL5CWApr9HOjkiyjgs/I49RZD+ZzG58CQQDwJuKi6J5rrUhhpqhH
5DuhhjOh7zNqojNVAlnT9tDt3L5IW4dPR51BxImEA00qCsQgjrq3B2kTJxk8BRDr
IZTtAkAP1bZBFmoKhOnENPrOhIk1lfuWxC3UFShcBCi0TEKKeEhKUH75ZxTCFc4L
reIdxe7/2a27YhE7RUwUdAesXFPBAkEA3rAAKnYwKMLnQn3Kv9dYoEAUcs2fTPsZ
RHPIni/ZryepXulYwGA053560epJzHltQo93fi8l9TelQ62i8ZYTRQJAfI4Al5tb
IWjAoIwB/+24s0kMHktLiMKF1cJJVuwsR4U5BkA4mhjYiRa6UcZitro/PjzrN1/d
U0w6nGai7j6b5Q==
-----END PRIVATE KEY-----"""


class AnsibleExitJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs
        super().__init__("AnsibleExitJson")


class AnsibleFailJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs
        super().__init__(kwargs.get("msg", "AnsibleFailJson"))


@pytest.fixture(scope="module")
def unifi_server():
    server = MockUniFiServer()
    yield server
    server.stop()


def run_test_module(module_func: Any, params: dict[str, Any], check_mode: bool = False) -> dict[str, Any]:
    module_class_path = f"{module_func.__module__}.AnsibleModule"
    with patch(module_class_path) as mock_cls:
        mock_module = MagicMock()
        mock_module.check_mode = check_mode
        mock_module._diff = True

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
            merged_params: dict[str, Any] = {}
            for param_name, spec in argument_spec.items():
                if "default" in spec:
                    merged_params[param_name] = spec["default"]
                else:
                    merged_params[param_name] = None
            merged_params.update(params)
            mock_module.params = merged_params
            mock_module.argument_spec = argument_spec
            return mock_module

        mock_cls.side_effect = mock_init

        try:
            module_func()
        except AnsibleExitJson:
            pass

        return result


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


def test_auth_api_key_mode(unifi_server: MockUniFiServer) -> None:
    """Verify module can authenticate with UniFi OS 3+ API key without session login."""
    unifi_server.reset()

    params = {
        "host": unifi_server.url,
        "api_key": "test-api-key",
        "site": "default",
        "validate_certs": False,
        "name": "APIKey-Firewall-Group",
        "group_type": "port-group",
        "group_members": ["8080"],
        "state": "present",
    }

    res = run_test_module(run_firewall_group, params)
    assert res.get("changed") is True
    # Verify no login request was sent to /api/auth/login
    login_reqs = [r for r in unifi_server.state.requests_log if r["path"] == "/api/auth/login"]
    assert len(login_reqs) == 0


def test_auth_session_cookie_mode(unifi_server: MockUniFiServer) -> None:
    """Verify module works with pre-authenticated session cookie & CSRF token."""
    unifi_server.reset()

    params = {
        "host": unifi_server.url,
        "unifi_session_cookie": "SESSION=session_cookie_abc",
        "unifi_csrf_token": "extracted_csrf_token_123",
        "site": "default",
        "validate_certs": False,
        "name": "Session-Firewall-Group",
        "group_type": "address-group",
        "group_members": ["192.168.1.10"],
        "state": "present",
    }

    res = run_test_module(run_firewall_group, params)
    assert res.get("changed") is True


def test_auth_invalid_credentials_fails(unifi_server: MockUniFiServer) -> None:
    """Verify failure handling when invalid credentials are provided."""
    unifi_server.reset()

    params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "wrongpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Bad-Auth-Group",
        "state": "present",
    }

    with pytest.raises(AnsibleFailJson) as exc_info:
        run_test_module(run_firewall_group, params)
    assert "invalid credentials" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Module End-to-End Tests: Network & Firewall Resources
# ---------------------------------------------------------------------------


def test_firewall_group_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_firewall_group create -> idempotency -> update -> check_mode -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Integration-Web-Ports",
        "group_type": "port-group",
        "group_members": ["80", "443"],
        "state": "present",
    }

    # 1. Check mode on create
    check_create = run_test_module(run_firewall_group, base_params, check_mode=True)
    assert check_create.get("changed") is True
    assert len(unifi_server.state.sites["default"]["firewallgroup"]) == 0

    # 2. Real create
    res = run_test_module(run_firewall_group, base_params)
    assert res.get("changed") is True
    assert len(unifi_server.state.sites["default"]["firewallgroup"]) == 1

    # 3. Idempotency
    res_idem = run_test_module(run_firewall_group, base_params)
    assert res_idem.get("changed") is False

    # 4. Update
    upd_params = dict(base_params, group_members=["80", "443", "8443"])
    res_upd = run_test_module(run_firewall_group, upd_params)
    assert res_upd.get("changed") is True

    # 5. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_firewall_group, del_params)
    assert res_del.get("changed") is True
    assert len(unifi_server.state.sites["default"]["firewallgroup"]) == 0

    # 6. Idempotent delete
    res_del_idem = run_test_module(run_firewall_group, del_params)
    assert res_del_idem.get("changed") is False


def test_firewall_zone_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_firewall_zone create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "DMZ",
        "network_ids": ["net_default_lan"],
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_firewall_zone, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_firewall_zone, base_params)
    assert res_idem.get("changed") is False

    # 3. Update: Rename zone via ID
    created_id = res["zone"]["_id"]
    upd_params = dict(base_params, id=created_id, name="DMZ-Renamed")
    res_upd = run_test_module(run_firewall_zone, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, name="DMZ-Renamed", state="absent")
    res_del = run_test_module(run_firewall_zone, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent delete
    res_del_idem = run_test_module(run_firewall_zone, del_params)
    assert res_del_idem.get("changed") is False


def test_firewall_policy_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_firewall_policy create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Allow-Web-Policy",
        "action": "ALLOW",
        "source": {"zone": "Internal"},
        "destination": {"zone": "External"},
        "state": "present",
    }

    # 1. Check mode
    res_chk = run_test_module(run_firewall_policy, base_params, check_mode=True)
    assert res_chk.get("changed") is True
    assert len(unifi_server.state.sites["default"]["firewall-policies"]) == 0

    # 2. Create
    res = run_test_module(run_firewall_policy, base_params)
    assert res.get("changed") is True
    assert len(unifi_server.state.sites["default"]["firewall-policies"]) == 1

    # 3. Idempotency
    res_idem = run_test_module(run_firewall_policy, base_params)
    assert res_idem.get("changed") is False

    # 4. Update
    upd_params = dict(base_params, action="DROP")
    res_upd = run_test_module(run_firewall_policy, upd_params)
    assert res_upd.get("changed") is True

    # 5. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_firewall_policy, del_params)
    assert res_del.get("changed") is True

    # 6. Idempotent delete
    res_del_idem = run_test_module(run_firewall_policy, del_params)
    assert res_del_idem.get("changed") is False


def test_nat_rule_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_nat_rule create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Integration-NAT-Rule",
        "type": "masquerade",
        "src_address": "192.168.1.0/24",
        "outbound_interface": "Default LAN",
        "enabled": True,
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_nat_rule, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_nat_rule, base_params)
    assert res_idem.get("changed") is False

    # 3. Update
    upd_params = dict(base_params, enabled=False)
    res_upd = run_test_module(run_nat_rule, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_nat_rule, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent delete
    res_del_idem = run_test_module(run_nat_rule, del_params)
    assert res_del_idem.get("changed") is False


def test_port_forward_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_port_forward create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Web-Forward-80",
        "proto": "tcp",
        "dst_port": "8080",
        "fwd_ip": "192.168.1.20",
        "fwd_port": "80",
        "enabled": True,
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_port_forward, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_port_forward, base_params)
    assert res_idem.get("changed") is False

    # 3. Update
    upd_params = dict(base_params, fwd_port="8081")
    res_upd = run_test_module(run_port_forward, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_port_forward, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent delete
    res_del_idem = run_test_module(run_port_forward, del_params)
    assert res_del_idem.get("changed") is False


def test_port_profile_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_port_profile create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Custom-Port-Profile",
        "forward": "native",
        "native_networkconf_id": "net_default_lan",
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_port_profile, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_port_profile, base_params)
    assert res_idem.get("changed") is False

    # 3. Update
    upd_params = dict(base_params, autoneg=False)
    res_upd = run_test_module(run_port_profile, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_port_profile, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent delete
    res_del_idem = run_test_module(run_port_profile, del_params)
    assert res_del_idem.get("changed") is False


def test_switch_profile_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_switch_profile create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Custom-Switch-Profile",
        "native_networkconf_id": "net_default_lan",
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_switch_profile, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_switch_profile, base_params)
    assert res_idem.get("changed") is False

    # 3. Update
    upd_params = dict(base_params, description="Custom updated switch profile")
    res_upd = run_test_module(run_switch_profile, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_switch_profile, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent delete
    res_del_idem = run_test_module(run_switch_profile, del_params)
    assert res_del_idem.get("changed") is False


def test_switch_profile_assignment_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_switch_profile_assignment port assignment and idempotency."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "switch_name": "Core-Switch-24",
        "profile_name": "All",
    }

    # 1. Check mode
    res_chk = run_test_module(run_switch_profile_assignment, base_params, check_mode=True)
    assert res_chk.get("changed") is True

    # 2. Assign
    res = run_test_module(run_switch_profile_assignment, base_params)
    assert res.get("changed") is True

    # 3. Idempotency
    res_idem = run_test_module(run_switch_profile_assignment, base_params)
    assert res_idem.get("changed") is False


def test_wlan_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_wlan create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Integration-SSID",
        "security": "wpapsk",
        "passphrase": "CorrectHorseBatteryStaple123",
        "enabled": True,
        "state": "present",
    }

    # 1. Create
    res = run_test_module(run_wlan, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_wlan, base_params)
    assert res_idem.get("changed") is False

    # 3. Update
    upd_params = dict(base_params, enabled=False)
    res_upd = run_test_module(run_wlan, upd_params)
    assert res_upd.get("changed") is True

    # 4. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_wlan, del_params)
    assert res_del.get("changed") is True


def test_network_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_network create -> idempotency -> update -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "name": "Integration-VLAN-20",
        "purpose": "corporate",
        "vlan": 20,
        "ip_subnet": "192.168.20.1/24",
        "dhcpd_enabled": True,
        "dhcp_start": "192.168.20.10",
        "dhcp_stop": "192.168.20.200",
        "state": "present",
    }

    # 1. Check mode on create
    res_chk = run_test_module(run_network, base_params, check_mode=True)
    assert res_chk.get("changed") is True
    existing = [n for n in unifi_server.state.sites["default"]["networkconf"] if n.get("name") == "Integration-VLAN-20"]
    assert len(existing) == 0

    # 2. Real create
    res = run_test_module(run_network, base_params)
    assert res.get("changed") is True
    existing = [n for n in unifi_server.state.sites["default"]["networkconf"] if n.get("name") == "Integration-VLAN-20"]
    assert len(existing) == 1
    assert existing[0]["vlan"] == "20"

    # 3. Idempotency
    res_idem = run_test_module(run_network, base_params)
    assert res_idem.get("changed") is False

    # 4. Update
    upd_params = dict(base_params, igmp_snooping=True)
    res_upd = run_test_module(run_network, upd_params)
    assert res_upd.get("changed") is True

    # 5. Delete
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_network, del_params)
    assert res_del.get("changed") is True
    existing = [n for n in unifi_server.state.sites["default"]["networkconf"] if n.get("name") == "Integration-VLAN-20"]
    assert len(existing) == 0

    # 6. Idempotent delete
    res_del_idem = run_test_module(run_network, del_params)
    assert res_del_idem.get("changed") is False


def test_dhcp_server_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_dhcp_server configuration update and idempotency on existing network."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "network": "Default LAN",
        "enabled": True,
        "dhcp_start": "192.168.1.50",
        "dhcp_stop": "192.168.1.150",
    }

    # 1. Check mode
    res_chk = run_test_module(run_dhcp_server, base_params, check_mode=True)
    assert res_chk.get("changed") is True

    # 2. Apply update
    res = run_test_module(run_dhcp_server, base_params)
    assert res.get("changed") is True

    # 3. Idempotency
    res_idem = run_test_module(run_dhcp_server, base_params)
    assert res_idem.get("changed") is False


def test_dhcp_reservation_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_dhcp_reservation assign fixed IP -> idempotency -> update -> release."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Office Printer",
        "fixed_ip": "192.168.1.75",
        "network_name": "Default LAN",
        "state": "present",
    }

    # 1. Set fixed IP reservation
    res = run_test_module(run_dhcp_reservation, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_dhcp_reservation, base_params)
    assert res_idem.get("changed") is False

    # 3. Update IP
    upd_params = dict(base_params, fixed_ip="192.168.1.76")
    res_upd = run_test_module(run_dhcp_reservation, upd_params)
    assert res_upd.get("changed") is True

    # 4. Remove reservation (state=absent)
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_dhcp_reservation, del_params)
    assert res_del.get("changed") is True

    # 5. Idempotent remove
    res_del_idem = run_test_module(run_dhcp_reservation, del_params)
    assert res_del_idem.get("changed") is False


def test_rsyslog_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_rsyslog configure -> idempotency."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "enabled": True,
        "ip": "192.168.1.200",
        "port": 514,
    }

    # 1. Update rsyslog
    res = run_test_module(run_rsyslog, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_rsyslog, base_params)
    assert res_idem.get("changed") is False


def test_system_settings_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_system_settings configure NTP & mgmt -> idempotency."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "ntp": {"server_1": "1.pool.ntp.org", "timezone": "Europe/Berlin"},
        "mgmt": {"led_enabled": False},
    }

    # 1. Apply system settings
    res = run_test_module(run_system_settings, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_system_settings, base_params)
    assert res_idem.get("changed") is False


def test_ssh_key_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_ssh_key add key -> idempotency -> delete key."""
    unifi_server.reset()

    key_value = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIntegrationKeyExample123 comment@example"
    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "keys": [key_value],
        "state": "present",
    }

    # 1. Add SSH Key
    res = run_test_module(run_ssh_key, base_params)
    assert res.get("changed") is True

    # 2. Idempotency
    res_idem = run_test_module(run_ssh_key, base_params)
    assert res_idem.get("changed") is False

    # 3. Remove SSH Key
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_ssh_key, del_params)
    assert res_del.get("changed") is True

    # 4. Idempotent remove
    res_del_idem = run_test_module(run_ssh_key, del_params)
    assert res_del_idem.get("changed") is False


def test_user_certificate_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_user_certificate upload -> idempotency -> delete."""
    unifi_server.reset()

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "validate_certs": False,
        "name": "Integration-Portal-Cert",
        "cert": TEST_CERT,
        "key": TEST_KEY,
        "active": True,
        "state": "present",
    }

    # 1. Upload certificate
    res = run_test_module(run_user_certificate, base_params)
    assert res.get("changed") is True
    assert len(unifi_server.state.user_certificates) == 1

    # 2. Idempotency
    res_idem = run_test_module(run_user_certificate, base_params)
    assert res_idem.get("changed") is False

    # 3. Delete certificate
    del_params = dict(base_params, state="absent")
    res_del = run_test_module(run_user_certificate, del_params)
    assert res_del.get("changed") is True
    assert len(unifi_server.state.user_certificates) == 0

    # 4. Idempotent delete
    res_del_idem = run_test_module(run_user_certificate, del_params)
    assert res_del_idem.get("changed") is False


def test_info_gather_subsets(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_info gathers facts across all supported resource categories."""
    unifi_server.reset()

    params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "gather_subset": [
            "wifi",
            "firewall_groups",
            "firewall_zones",
            "firewall_policies",
            "port_profiles",
            "devices",
            "networks",
            "system_settings",
            "port_forward",
        ],
    }

    res = run_test_module(run_info, params)
    assert "unifi_info" in res
    info = res["unifi_info"]

    assert "wifi" in info
    assert "firewall_groups" in info
    assert "firewall_zones" in info
    assert "firewall_policies" in info
    assert "port_profiles" in info
    assert "devices" in info
    assert "networks" in info
    assert "system_settings" in info
    assert "port_forward" in info


def test_device_lifecycle(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_device adopt -> idempotency -> update -> absent."""
    unifi_server.reset()

    # Pre-populate an unadopted device in the controller
    device_mac = "70:a7:41:99:88:77"
    raw_device = {
        "_id": "dev_test_ap_1",
        "mac": device_mac,
        "name": "",
        "model": "U6-Pro",
        "type": "uap",
        "ip": "192.168.1.120",
        "version": "6.6.55",
        "adopted": False,
        "state": 2,
        "disabled": False,
        "led_override": "default",
    }
    unifi_server.state.get_site_collection("default", "device").append(raw_device)

    base_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "mac": device_mac,
        "name": "AP-ConferenceRoom",
        "adopt": True,
        "led_override": "off",
        "state": "present",
    }

    # 1. Check mode
    res_chk = run_test_module(run_device, base_params, check_mode=True)
    assert res_chk.get("changed") is True
    assert res_chk.get("diff", {}).get("after", {}).get("name") == "AP-ConferenceRoom"

    # 2. Adopt & configure
    res = run_test_module(run_device, base_params)
    assert res.get("changed") is True
    assert res.get("device", {}).get("name") == "AP-ConferenceRoom"
    assert res.get("device", {}).get("led_override") == "off"

    # 3. Idempotency
    res_idem = run_test_module(run_device, base_params)
    assert res_idem.get("changed") is False

    # 4. Update (rename and enable note)
    upd_params = dict(base_params, name="AP-Boardroom", note="Boardroom Ceiling")
    res_upd = run_test_module(run_device, upd_params)
    assert res_upd.get("changed") is True
    assert res_upd.get("device", {}).get("name") == "AP-Boardroom"
    assert res_upd.get("device", {}).get("note") == "Boardroom Ceiling"

    # 5. Delete / Forget
    del_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
        "mac": device_mac,
        "state": "absent",
    }
    res_del = run_test_module(run_device, del_params)
    assert res_del.get("changed") is True

    # 6. Idempotent delete
    res_del_idem = run_test_module(run_device, del_params)
    assert res_del_idem.get("changed") is False


def test_login_integration(unifi_server: MockUniFiServer) -> None:
    """Verify unifi_login produces valid reusable session tokens for subsequent modules."""
    unifi_server.reset()

    # 1. Check mode
    chk_params = {
        "host": unifi_server.url,
        "username": "admin",
        "password": "secretpassword",
        "site": "default",
        "validate_certs": False,
    }
    res_chk = run_test_module(run_login, chk_params, check_mode=True)
    assert res_chk.get("changed") is False
    assert "unifi_session" in res_chk
    assert res_chk["unifi_session"]["session_cookie"] == "check-mode-cookie"

    # 2. Real login execution
    res_login = run_test_module(run_login, chk_params)
    assert res_login.get("changed") is False
    assert "unifi_session" in res_login
    session = res_login["unifi_session"]
    assert "session_cookie" in session and session["session_cookie"]
    assert "csrf_token" in session and session["csrf_token"]
    assert len(session.get("sites", [])) >= 1

    # 3. Use returned tokens in another module without providing username/password
    wlan_params = {
        "host": unifi_server.url,
        "unifi_session_cookie": session["session_cookie"],
        "unifi_csrf_token": session["csrf_token"],
        "site": session["site"],
        "validate_certs": False,
        "name": "TokenAuthWiFi",
        "passphrase": "supersecurepassword123",
        "state": "present",
    }
    res_wlan = run_test_module(run_wlan, wlan_params)
    assert res_wlan.get("changed") is True
    assert res_wlan.get("wlan", {}).get("name") == "TokenAuthWiFi"
