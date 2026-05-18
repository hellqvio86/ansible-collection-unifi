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
        default: false
        type: bool
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

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        network=dict(type="str", required=True),
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
    )
    api.login()

    site = module.params["site"]

    res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    if info["status"] != 200:
        module.fail_json(msg="Failed to fetch network configurations", info=info)

    networks = api.as_list(res)
    current = next(
        (n for n in networks if isinstance(n, dict) and n.get("name") == network_name),
        None,
    )
    if not current:
        module.fail_json(msg=f"Network '{network_name}' not found")

    desired_payload = {
        "dhcpd_enabled": enabled,
    }

    if module.params["dhcp_start"] is not None:
        desired_payload["dhcpd_start"] = module.params["dhcp_start"]
    if module.params["dhcp_stop"] is not None:
        desired_payload["dhcpd_stop"] = module.params["dhcp_stop"]
    if module.params["lease_time"] is not None:
        desired_payload["dhcpd_leasetime"] = module.params["lease_time"]
    if module.params["dns_1"] is not None:
        desired_payload["dhcpd_dns_1"] = module.params["dns_1"]
    if module.params["dns_2"] is not None:
        desired_payload["dhcpd_dns_2"] = module.params["dns_2"]
    if module.params["gateway"] is not None:
        desired_payload["dhcpd_gateway"] = module.params["gateway"]
    if module.params["domain"] is not None:
        desired_payload["dhcpd_domain_name"] = module.params["domain"]

    dhcp_fields = [
        "dhcpd_enabled",
        "dhcpd_start",
        "dhcpd_stop",
        "dhcpd_leasetime",
        "dhcpd_dns_1",
        "dhcpd_dns_2",
        "dhcpd_gateway",
        "dhcpd_domain_name",
    ]

    changed = False
    for field in dhcp_fields:
        if field in desired_payload:
            current_value = current.get(field)
            desired_value = desired_payload[field]
            if field == "dhcpd_enabled":
                desired_value = bool(desired_value)
            if current_value != desired_value:
                changed = True
                break

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
                current = res_list[0]

    module.exit_json(changed=changed, network=current)


if __name__ == "__main__":
    run_module()
