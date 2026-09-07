#!/usr/bin/python
# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: unifi_network
short_description: Manage networks and VLANs on a UniFi controller
version_added: "0.0.32"
description:
    - Create, update, or remove networks and VLANs on a UniFi controller.
    - Supports corporate routed networks, isolated guest networks, and pure Layer-2 VLAN-only networks.
    - Configures IP subnets, VLAN IDs, DHCP server settings, DNS overrides, and network features.
    - Uses the official UniFi REST endpoint C(/proxy/network/api/s/{site}/rest/networkconf).
options:
    host:
        description: The host or IP address of the UniFi controller.
        required: false
        type: str
    username:
        description: UniFi controller username.
        required: false
        type: str
    password:
        description: UniFi controller password.
        required: false
        type: str
    site:
        description: UniFi site name.
        default: default
        type: str
    validate_certs:
        description: Verify SSL certificates.
        default: true
        type: bool
    api_key:
        description:
            - Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+).
            - Preferred over username/password.
            - Can also be set via the C(UNIFI_API_KEY) or C(UNIFI_API_TOKEN) environment variables.
        type: str
        required: false
    ca_path:
        description: Path to CA bundle file for TLS verification.
        required: false
        type: path
    unifi_session_cookie:
        description: Pre-authenticated session cookie string.
        type: str
        required: false
    unifi_csrf_token:
        description: Pre-authenticated CSRF token.
        type: str
        required: false
    state:
        description: Whether the network should exist or be removed.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the network or VLAN.
        required: true
        type: str
    id:
        description: Unique identifier of the network for explicit ID-based targeting or renaming.
        required: false
        type: str
    purpose:
        description:
            - Network purpose / type.
            - C(corporate) is a standard internal routed network.
            - C(guest) is an isolated guest network.
            - C(vlan-only) is a Layer-2 tagged VLAN without routing or DHCP on the gateway.
            - C(wan) represents a WAN interface uplink.
        choices: [ corporate, guest, vlan-only, wan ]
        default: corporate
        type: str
    vlan:
        description:
            - VLAN ID (tag number) between 1 and 4094.
            - Setting this enables VLAN tagging on the network.
        required: false
        type: int
    vlan_enabled:
        description:
            - Explicitly enable or disable VLAN tagging.
            - Automatically set to true if C(vlan) is specified and > 1.
        required: false
        type: bool
    ip_subnet:
        description:
            - Gateway IP address and CIDR prefix (e.g., C(192.168.20.1/24)).
            - Required for C(corporate) and C(guest) networks when C(state=present).
        required: false
        type: str
    domain_name:
        description:
            - Local domain name suffix for clients on this network (e.g., C(lan.local)).
        required: false
        type: str
    enabled:
        description: Whether the network is enabled.
        default: true
        type: bool
    dhcpd_enabled:
        description:
            - Enable the built-in DHCP server for this network.
            - Only applicable to C(corporate) and C(guest) networks.
        required: false
        type: bool
    dhcp_start:
        description: Start IP address for the DHCP range (e.g., C(192.168.20.10)).
        required: false
        type: str
    dhcp_stop:
        description: End IP address for the DHCP range (e.g., C(192.168.20.200)).
        required: false
        type: str
    dhcp_lease_time:
        description: DHCP lease time in seconds (e.g., 86400).
        required: false
        type: int
    dhcp_dns_1:
        description: Primary DNS server IP for DHCP clients.
        required: false
        type: str
    dhcp_dns_2:
        description: Secondary DNS server IP for DHCP clients.
        required: false
        type: str
    dhcp_gateway:
        description: Gateway IP override distributed via DHCP.
        required: false
        type: str
    dhcp_guarding:
        description: Enable DHCP Guarding to block rogue DHCP servers.
        required: false
        type: bool
    dhcp_guarding_servers:
        description: List of trusted DHCP server IP addresses when DHCP guarding is enabled.
        required: false
        type: list
        elements: str
    igmp_snooping:
        description: Enable IGMP snooping on switches for this network.
        required: false
        type: bool
    multicast_dns:
        description: Enable Multicast DNS (mDNS) reflector for this network.
        required: false
        type: bool
    networkgroup:
        description: Network group assignment.
        choices: [ LAN, WAN ]
        default: LAN
        type: str
author:
    - Olof Hellqvist (@hellqvio86)
"""

EXAMPLES = r"""
- name: Create a corporate VLAN network
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "IoT Network"
    purpose: "corporate"
    vlan: 20
    ip_subnet: "192.168.20.1/24"
    dhcpd_enabled: true
    dhcp_start: "192.168.20.10"
    dhcp_stop: "192.168.20.200"
    state: present

- name: Create a Layer-2 VLAN-only network for third-party router
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "CCTV VLAN"
    purpose: "vlan-only"
    vlan: 50
    state: present

- name: Remove a VLAN network
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "CCTV VLAN"
    state: absent
"""

RETURN = r"""
changed:
    description: Whether the network was created, updated, or removed.
    type: bool
    returned: always
network:
    description: Current state of the network configuration.
    type: dict
    returned: always
    sample:
        _id: "60f1b2c3d4e5f6a7b8c9d0e1"
        name: "IoT Network"
        purpose: "corporate"
        vlan: 20
        vlan_enabled: true
        ip_subnet: "192.168.20.1/24"
        dhcpd_enabled: true
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
    UnifiAPI,
    find_resource,
    make_diff,
    resource_has_drift,
    validate_cidr,
    validate_ip_address,
)


def _build_desired_payload(params: dict[str, Any]) -> dict[str, Any]:
    """Build the desired networkconf payload from module parameters."""
    purpose = params["purpose"]
    name = params["name"]
    enabled = params.get("enabled", True)
    networkgroup = params.get("networkgroup", "LAN")

    payload: dict[str, Any] = {
        "name": name,
        "purpose": purpose,
        "enabled": enabled,
        "networkgroup": networkgroup,
    }

    # VLAN settings
    vlan = params.get("vlan")
    vlan_enabled = params.get("vlan_enabled")

    if vlan is not None:
        payload["vlan"] = str(vlan) if purpose != "vlan-only" else str(vlan)
        if vlan_enabled is not None:
            payload["vlan_enabled"] = vlan_enabled
        else:
            payload["vlan_enabled"] = bool(vlan and vlan > 1)
    elif vlan_enabled is not None:
        payload["vlan_enabled"] = vlan_enabled

    # Routing & Subnet (corporate and guest)
    if purpose in ("corporate", "guest"):
        if params.get("ip_subnet"):
            payload["ip_subnet"] = params["ip_subnet"]

        if params.get("domain_name") is not None:
            payload["domain_name"] = params["domain_name"]
            payload["dhcpd_domain_name"] = params["domain_name"]

        # DHCP settings
        if params.get("dhcpd_enabled") is not None:
            payload["dhcpd_enabled"] = params["dhcpd_enabled"]
        if params.get("dhcp_start") is not None:
            payload["dhcpd_start"] = params["dhcp_start"]
        if params.get("dhcp_stop") is not None:
            payload["dhcpd_stop"] = params["dhcp_stop"]
        if params.get("dhcp_lease_time") is not None:
            payload["dhcpd_leasetime"] = params["dhcp_lease_time"]
        if params.get("dhcp_dns_1") is not None:
            payload["dhcpd_dns_1"] = params["dhcp_dns_1"]
            payload["dhcpd_dns_enabled"] = True
        if params.get("dhcp_dns_2") is not None:
            payload["dhcpd_dns_2"] = params["dhcp_dns_2"]
            payload["dhcpd_dns_enabled"] = True
        if params.get("dhcp_gateway") is not None:
            payload["dhcpd_gateway"] = params["dhcp_gateway"]

        # DHCP Guarding
        if params.get("dhcp_guarding") is not None:
            payload["dhcp_guard_enabled"] = params["dhcp_guarding"]
        if params.get("dhcp_guarding_servers") is not None:
            payload["dhcp_guard_servers"] = params["dhcp_guarding_servers"]

    # Switching & Multicast features
    if params.get("igmp_snooping") is not None:
        payload["igmp_snooping"] = params["igmp_snooping"]
    if params.get("multicast_dns") is not None:
        payload["mdns_enabled"] = params["multicast_dns"]

    return payload


def run_module() -> None:
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        id=dict(type="str", required=False),
        purpose=dict(type="str", choices=["corporate", "guest", "vlan-only", "wan"], default="corporate"),
        vlan=dict(type="int", required=False),
        vlan_enabled=dict(type="bool", required=False),
        ip_subnet=dict(type="str", required=False),
        domain_name=dict(type="str", required=False),
        enabled=dict(type="bool", default=True),
        dhcpd_enabled=dict(type="bool", required=False),
        dhcp_start=dict(type="str", required=False),
        dhcp_stop=dict(type="str", required=False),
        dhcp_lease_time=dict(type="int", required=False),
        dhcp_dns_1=dict(type="str", required=False),
        dhcp_dns_2=dict(type="str", required=False),
        dhcp_gateway=dict(type="str", required=False),
        dhcp_guarding=dict(type="bool", required=False),
        dhcp_guarding_servers=dict(type="list", elements="str", required=False),
        igmp_snooping=dict(type="bool", required=False),
        multicast_dns=dict(type="bool", required=False),
        networkgroup=dict(type="str", choices=["LAN", "WAN"], default="LAN"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Input validations
    state = module.params["state"]
    purpose = module.params["purpose"]
    name = module.params["name"]
    vlan = module.params.get("vlan")

    if vlan is not None and not (1 <= vlan <= 4094):
        module.fail_json(msg=f"VLAN ID '{vlan}' must be an integer between 1 and 4094")

    if state == "present":
        if purpose in ("corporate", "guest"):
            if not module.params.get("ip_subnet"):
                module.fail_json(msg=f"'ip_subnet' is required for network purpose '{purpose}'")
            validate_cidr(module, module.params["ip_subnet"], "ip_subnet")

        for ip_param in ("dhcp_start", "dhcp_stop", "dhcp_dns_1", "dhcp_dns_2", "dhcp_gateway"):
            val = module.params.get(ip_param)
            if val:
                validate_ip_address(module, val, ip_param)

        if module.params.get("dhcp_guarding_servers"):
            for srv in module.params["dhcp_guarding_servers"]:
                validate_ip_address(module, srv, "dhcp_guarding_servers")

    api = UnifiAPI(
        module,
        module.params.get("host"),
        module.params.get("username"),
        module.params.get("password"),
        module.params.get("validate_certs"),
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    site = module.params["site"]
    networkconf_url = f"/proxy/network/api/s/{site}/rest/networkconf"

    # Fetch existing networks
    res, info = api.request(networkconf_url)
    if info.get("status") != 200:
        module.fail_json(msg="Failed to fetch existing networks", info=info)

    networks = api.as_list(res)
    existing = find_resource(module, networks, "network", name=name, resource_id=module.params.get("id"))

    changed = False
    result_network = existing
    desired_payload = _build_desired_payload(module.params)

    if state == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                post_res, post_info = api.request(networkconf_url, method="POST", data=desired_payload)
                if post_info.get("status") not in (200, 201):
                    module.fail_json(msg="Failed to create network", info=post_info)
                created_list = api.as_list(post_res)
                result_network = created_list[0] if created_list else post_res
            else:
                result_network = desired_payload
        else:
            if resource_has_drift(existing, desired_payload):
                changed = True
                if not module.check_mode:
                    put_url = f"{networkconf_url}/{existing['_id']}"
                    put_res, put_info = api.request(put_url, method="PUT", data=desired_payload)
                    if put_info.get("status") not in (200, 201):
                        module.fail_json(msg="Failed to update network", info=put_info)
                    updated_list = api.as_list(put_res)
                    result_network = updated_list[0] if updated_list else put_res
                else:
                    result_network = {**existing, **desired_payload}

    elif state == "absent":
        if existing:
            if existing.get("default") is True or existing.get("attr_no_delete") is True:
                module.fail_json(msg=f"Cannot delete default or protected system network '{name}'")

            changed = True
            if not module.check_mode:
                del_url = f"{networkconf_url}/{existing['_id']}"
                del_res, del_info = api.request(del_url, method="DELETE")
                if del_info.get("status") not in (200, 204):
                    module.fail_json(msg="Failed to delete network", info=del_info)
                result_network = {}
            else:
                result_network = {}

    exit_kwargs: dict[str, Any] = {"changed": changed, "network": result_network}
    if getattr(module, "_diff", False) is True:
        before = existing if existing else {}
        after = result_network if result_network else {}
        exit_kwargs["diff"] = make_diff(before, after)

    module.exit_json(**exit_kwargs)


if __name__ == "__main__":
    run_module()
