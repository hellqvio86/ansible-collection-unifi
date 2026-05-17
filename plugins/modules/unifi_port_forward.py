#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_port_forward
short_description: Manage UniFi port forwarding rules
version_added: "0.0.9"
description:
    - Create, update, or delete port forwarding rules on a UniFi controller.
    - Uses the C(/proxy/network/api/s/{site}/rest/portforward) endpoint.
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
            - Whether the rule should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description:
            - Name of the port forwarding rule.
        required: true
        type: str
    enabled:
        description:
            - Whether the rule is enabled.
        default: true
        type: bool
    protocol:
        description:
            - IP protocol to match.
        choices: [ tcp, udp, tcp_udp ]
        default: tcp_udp
        type: str
    src:
        description:
            - Source IP or CIDR to match.
            - Empty string matches any source.
        default: ""
        type: str
    dst_port:
        description:
            - Destination port on the WAN interface (e.g., C(2222)).
        required: true
        type: str
    fwd_port:
        description:
            - Port to forward traffic to on the internal host.
            - If not set, defaults to the value of C(dst_port).
        required: false
        type: str
    fwd_ip:
        description:
            - IP address of the internal host to forward to.
        required: true
        type: str
    fwd_network:
        description:
            - Name of the network the internal host is on.
            - If not set, the rule applies to the Default network.
        required: false
        type: str
    log:
        description:
            - Whether to log forwarded connections.
        type: bool
        default: false
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Create SSH port forward on non-standard port
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "SSH to Server"
    enabled: true
    protocol: tcp
    dst_port: "2222"
    fwd_port: "22"
    fwd_ip: "192.168.1.10"
    fwd_network: "Default"

- name: Disable a port forward rule
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "SSH to Server"
    enabled: false

- name: Delete a port forward rule
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Old Rule"
    state: absent
"""

RETURN = r"""
changed:
    description: Whether any change was applied.
    type: bool
    returned: always
rule:
    description: The current state of the port forwarding rule after the operation.
    type: dict
    returned: always
    sample: {"_id": "...", "name": "SSH to Server", "enabled": true, "dst_port": "2222", "fwd_ip": "192.168.1.10"}
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
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        enabled=dict(type="bool", default=True),
        protocol=dict(type="str", choices=["tcp", "udp", "tcp_udp"], default="tcp_udp"),
        src=dict(type="str", default=""),
        dst_port=dict(type="str", required=True),
        fwd_port=dict(type="str", required=False),
        fwd_ip=dict(type="str", required=True),
        fwd_network=dict(type="str", required=False),
        log=dict(type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

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
    name = module.params["name"]
    state = module.params["state"]
    dst_port = module.params["dst_port"]
    fwd_port = module.params["fwd_port"] or dst_port

    fwd_network_id = ""
    if module.params["fwd_network"]:
        net_res, net_info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
        if net_info["status"] != 200:
            module.fail_json(msg="Failed to fetch networks", info=net_info)
        networks = api.as_list(net_res)
        match = next(
            (n for n in networks if isinstance(n, dict) and n.get("name") == module.params["fwd_network"]),
            None,
        )
        if not match:
            module.fail_json(msg=f"Network '{module.params['fwd_network']}' not found")
        fwd_network_id = match["_id"]

    res, info = api.request(f"/proxy/network/api/s/{site}/rest/portforward")
    if info["status"] != 200:
        module.fail_json(msg="Failed to fetch port forwarding rules", info=info)

    rules = api.as_list(res)
    current = next((r for r in rules if isinstance(r, dict) and r.get("name") == name), None)

    if state == "absent":
        if current:
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portforward/{current['_id']}",
                    method="DELETE",
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete port forwarding rule", info=info)
            module.exit_json(changed=True, rule=None)
            return
        module.exit_json(changed=False, rule=None)
        return

    desired_payload = {
        "name": name,
        "enabled": module.params["enabled"],
        "proto": module.params["protocol"],
        "dst_port": dst_port,
        "fwd_port": fwd_port,
        "fwd_ip": module.params["fwd_ip"],
        "log": module.params["log"],
    }

    if module.params["src"]:
        desired_payload["src"] = module.params["src"]
    if fwd_network_id:
        desired_payload["fwd_network_id"] = fwd_network_id

    if current:
        changed = False
        if current.get("enabled") != desired_payload["enabled"]:
            changed = True
        elif current.get("proto") != desired_payload["proto"]:
            changed = True
        elif current.get("src", "") != (desired_payload.get("src") or ""):
            changed = True
        elif current.get("dst_port") != desired_payload["dst_port"]:
            changed = True
        elif current.get("fwd_port") != desired_payload["fwd_port"]:
            changed = True
        elif current.get("fwd_ip") != desired_payload["fwd_ip"]:
            changed = True
        elif current.get("fwd_network_id", "") != (desired_payload.get("fwd_network_id") or ""):
            changed = True
        elif current.get("log", False) != desired_payload["log"]:
            changed = True

        if changed:
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portforward/{current['_id']}",
                    method="PUT",
                    data=desired_payload,
                )
                if info["status"] not in [200, 201]:
                    module.fail_json(msg="Failed to update port forwarding rule", info=info)
                res_list = api.as_list(res)
                if res_list:
                    current = res_list[0]
            module.exit_json(changed=True, rule=current)
            return
        module.exit_json(changed=False, rule=current)
        return

    if not module.check_mode:
        res, info = api.request(
            f"/proxy/network/api/s/{site}/rest/portforward",
            method="POST",
            data=desired_payload,
        )
        if info["status"] not in [200, 201]:
            module.fail_json(msg="Failed to create port forwarding rule", info=info)
        res_list = api.as_list(res)
        if res_list:
            current = res_list[0]
    module.exit_json(changed=True, rule=current)


if __name__ == "__main__":
    run_module()
