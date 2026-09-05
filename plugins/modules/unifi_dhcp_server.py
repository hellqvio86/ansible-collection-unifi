#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_dhcp_server
short_description: Manage DHCP server settings on a UniFi network
version_added: "0.0.7"
description:
    - Configure DHCP server settings (range, lease time, DNS, gateway) for a network on a UniFi controller.
    - Uses the C(/proxy/network/api/s/{site}/rest/networkconf) endpoint to manage DHCP settings per network.
options:
    host:
        description: The host of the UniFi controller.
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
    state:
        description:
            - Whether DHCP server should be configured or disabled on the network.
            - C(present) ensures DHCP settings are applied.
            - C(absent) disables the DHCP server on the network.
        choices: [ present, absent ]
        default: present
        type: str
    network:
        description:
            - Name of the network (LAN) to configure DHCP on.
        required: true
        type: str
    enabled:
        description:
            - Whether the DHCP server is enabled on this network.
            - When C(state=absent), this is forced to C(false).
        default: true
        type: bool
    dhcp_start:
        description:
            - Start IP address of the DHCP range (e.g., C(192.168.1.100)).
            - Required when C(enabled=true) and C(state=present).
        required: false
        type: str
    dhcp_stop:
        description:
            - End IP address of the DHCP range (e.g., C(192.168.1.200)).
            - Required when C(enabled=true) and C(state=present).
        required: false
        type: str
    lease_time:
        description:
            - DHCP lease time in seconds.
        required: false
        type: int
    dns_1:
        description:
            - Primary DNS server IP address.
        required: false
        type: str
    dns_2:
        description:
            - Secondary DNS server IP address.
        required: false
        type: str
    gateway:
        description:
            - Gateway IP address override.
            - If not set, the network's configured gateway is used.
        required: false
        type: str
    domain:
        description:
            - DHCP domain name (e.g., C(lan.example.com)).
        required: false
        type: str
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Configure DHCP server on the Default network
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Default"
    enabled: true
    dhcp_start: "192.168.1.100"
    dhcp_stop: "192.168.1.200"
    lease_time: 86400
    dns_1: "192.168.1.1"
    dns_2: "8.8.8.8"

- name: Disable DHCP server on a network
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Guest"
    state: absent

- name: Update DNS servers only
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Default"
    enabled: true
    dns_1: "1.1.1.1"
    dns_2: "8.8.8.8"
"""

RETURN = r"""
changed:
    description: Whether any change was applied.
    type: bool
    returned: always
network:
    description: The current state of the network configuration after the operation.
    type: dict
    returned: always
    sample: {"_id": "...", "name": "Default", "dhcpd_enabled": true, "dhcpd_start": "192.168.1.100"}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
    UnifiAPI,
    find_resource,
    make_diff,
    resource_has_drift,
    validate_ip_address,
)


def _build_desired_payload(params: dict, enabled: bool) -> dict:
    """Build the desired DHCP server payload from module parameters."""
    payload: dict = {"dhcpd_enabled": enabled}
    if params.get("dhcp_start") is not None:
        payload["dhcpd_start"] = params["dhcp_start"]
    if params.get("dhcp_stop") is not None:
        payload["dhcpd_stop"] = params["dhcp_stop"]
    if params.get("lease_time") is not None:
        payload["dhcpd_leasetime"] = params["lease_time"]
    if params.get("dns_1") is not None:
        payload["dhcpd_dns_1"] = params["dns_1"]
    if params.get("dns_2") is not None:
        payload["dhcpd_dns_2"] = params["dns_2"]
    if params.get("gateway") is not None:
        payload["dhcpd_gateway"] = params["gateway"]
    if params.get("domain") is not None:
        payload["dhcpd_domain_name"] = params["domain"]
    return payload


def run_module():
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        network=dict(type="str", required=True),
        id=dict(type="str", required=False),
        enabled=dict(type="bool", default=True),
        dhcp_start=dict(type="str", required=False),
        dhcp_stop=dict(type="str", required=False),
        lease_time=dict(type="int", required=False),
        dns_1=dict(type="str", required=False),
        dns_2=dict(type="str", required=False),
        gateway=dict(type="str", required=False),
        domain=dict(type="str", required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    network_name = module.params["network"]
    state = module.params["state"]
    enabled = module.params["enabled"]

    if state == "absent":
        enabled = False

    if enabled:
        if not module.params["dhcp_start"]:
            module.fail_json(msg="'dhcp_start' is required when the DHCP server is enabled")
        if not module.params["dhcp_stop"]:
            module.fail_json(msg="'dhcp_stop' is required when the DHCP server is enabled")

    api = UnifiAPI(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"],
        module.params["validate_certs"],
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    # Validate argument formats before making any API calls
    if enabled:
        if module.params.get("dhcp_start"):
            validate_ip_address(module, module.params["dhcp_start"], "dhcp_start")
        if module.params.get("dhcp_stop"):
            validate_ip_address(module, module.params["dhcp_stop"], "dhcp_stop")
    if module.params.get("dns_1"):
        validate_ip_address(module, module.params["dns_1"], "dns_1")
    if module.params.get("dns_2"):
        validate_ip_address(module, module.params["dns_2"], "dns_2")
    if module.params.get("gateway"):
        validate_ip_address(module, module.params["gateway"], "gateway")

    site = module.params["site"]

    res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    if info["status"] != 200:
        module.fail_json(msg="Failed to fetch network configurations", info=info)

    networks = api.as_list(res)
    current = find_resource(
        module, networks, "network", name=network_name, resource_id=module.params.get("id")
    )
    if not current:
        module.fail_json(msg=f"Network '{network_name}' not found")

    desired_payload = _build_desired_payload(module.params, enabled)

    changed = resource_has_drift(current, desired_payload)

    result_network = current
    if changed:
        if not module.check_mode:
            res, info = api.request(
                f"/proxy/network/api/s/{site}/rest/networkconf/{current['_id']}",
                method="PUT",
                data=desired_payload,
            )
            if info["status"] not in [200, 201]:
                module.fail_json(msg="Failed to update DHCP server settings", info=info)
            res_list = api.as_list(res)
            if res_list:
                result_network = res_list[0]
            else:
                result_network = {**current, **desired_payload}
        else:
            result_network = {**current, **desired_payload}

    exit_kwargs = {"changed": changed, "network": result_network}
    if getattr(module, "_diff", False) is True:
        before = current if current else {}
        after = result_network if result_network else {}
        exit_kwargs["diff"] = make_diff(before, after)


    module.exit_json(**exit_kwargs)



if __name__ == "__main__":
    run_module()
