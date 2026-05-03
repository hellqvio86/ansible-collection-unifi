#!/usr/bin/python


DOCUMENTATION = r"""
---
module: unifi_firewall_policy
short_description: Manage UniFi v8.3+ Policy Engine Firewall Rules
version_added: "0.0.1"
description:
    - Create, update, or delete firewall policies in a UniFi controller using the modern Policy Engine (Zone-Based Firewall).
    - This module targets the v2 API introduced in UniFi Network 8.x.
options:
    host:
        description: The host of the UniFi controller (e.g., 192.168.1.1).
        required: true
        type: str
    username:
        description: UniFi controller username.
        required: true
        type: str
    password:
        description: UniFi controller password.
        required: true
        type: str
    site:
        description: UniFi site name (typically 'default').
        default: default
        type: str
    validate_certs:
        description: Verify SSL certificates.
        default: false
        type: bool
    state:
        description: Whether the policy should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the firewall policy.
        required: true
        type: str
    action:
        description: Action to take.
        choices: [ ALLOW, BLOCK, REJECT, ISOLATE ]
        default: ALLOW
        type: str
    protocol:
        description: Protocol to match.
        choices: [ all, tcp, udp, tcp_udp, icmp, icmpv6 ]
        default: all
        type: str
    index:
        description: Rule index (order).
        type: int
        default: 10000
    enabled:
        description: Whether the rule is enabled.
        type: bool
        default: true
    logging:
        description: Whether to log matches.
        type: bool
        default: false
    source:
        description: Source configuration.
        type: dict
        suboptions:
            zone:
                description: Source zone name (e.g., Internal, External, Guest).
                type: str
                default: Internal
            matching_target:
                description: Type of source to match.
                choices: [ ANY, IP, NETWORK, DOMAIN ]
                default: ANY
                type: str
            ips:
                description: List of IP addresses or subnets.
                type: list
                elements: str
            port:
                description: Port or port range.
                type: str
    destination:
        description: Destination configuration.
        type: dict
        suboptions:
            zone:
                description: Destination zone name.
                type: str
                default: Internal
            matching_target:
                description: Type of destination to match.
                choices: [ ANY, IP, NETWORK, DOMAIN ]
                default: ANY
                type: str
            ips:
                description: List of IP addresses or subnets.
                type: list
                elements: str
            port:
                description: Port or port range.
                type: str
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    policy_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        action=dict(type="str", choices=["ALLOW", "BLOCK", "REJECT", "ISOLATE"], default="ALLOW"),
        protocol=dict(type="str", choices=["all", "tcp", "udp", "tcp_udp", "icmp", "icmpv6"], default="all"),
        index=dict(type="int", default=10000),
        enabled=dict(type="bool", default=True),
        logging=dict(type="bool", default=False),
        source=dict(type="dict", default={}),
        destination=dict(type="dict", default={}),
    )
    module_args = dict(
        host=dict(type="str", required=True),
        username=dict(type="str", required=True, no_log=True),
        password=dict(type="str", required=True, no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=False),
        policies=dict(type="list", elements="dict", options=policy_spec),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str"),
        action=dict(type="str", choices=["ALLOW", "BLOCK", "REJECT", "ISOLATE"], default="ALLOW"),
        protocol=dict(type="str", choices=["all", "tcp", "udp", "tcp_udp", "icmp", "icmpv6"], default="all"),
        index=dict(type="int", default=10000),
        enabled=dict(type="bool", default=True),
        logging=dict(type="bool", default=False),
        source=dict(type="dict", default={}),
        destination=dict(type="dict", default={}),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    site = module.params["site"]
    validate_certs = module.params["validate_certs"]

    # 1. Initialize API and Login
    api = UnifiAPI(module, host, username, password, validate_certs)
    api.login()

    # 2. Resolve zones once for the full batch.
    zones_res, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall/zone")
    if zones_res is None:
        module.fail_json(msg="Failed to fetch zones", info=info)
    zones = zones_res.get("data", []) if isinstance(zones_res, dict) and "data" in zones_res else zones_res

    zone_map = {z["name"]: z["_id"] for z in zones}

    # 3. Resolve network names to IDs for NETWORK matching.
    networks_res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    if networks_res is None:
        module.fail_json(msg="Failed to fetch networks", info=info)
    networks = networks_res.get("data", []) if isinstance(networks_res, dict) and "data" in networks_res else networks_res

    network_map = {n["name"]: n["_id"] for n in networks}

    # 4. Fetch existing policies once. The old role loop caused one login and
    # one policy fetch per rule, which quickly trips UniFi API rate limits.
    policies_res, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall-policies")
    if policies_res is None:
        module.fail_json(msg="Failed to fetch policies", info=info)
    policies = policies_res.get("data", []) if isinstance(policies_res, dict) and "data" in policies_res else policies_res

    changed = False
    results = []
    desired_policies = module.params["policies"] or [
        {
            "state": module.params["state"],
            "name": module.params["name"],
            "action": module.params["action"],
            "protocol": module.params["protocol"],
            "index": module.params["index"],
            "enabled": module.params["enabled"],
            "logging": module.params["logging"],
            "source": module.params["source"],
            "destination": module.params["destination"],
        }
    ]

    if not module.params["policies"] and not module.params["name"]:
        module.fail_json(msg="Either name or policies is required")

    for desired in desired_policies:
        policy_changed, result_policy = apply_policy(module, api, site, zone_map, network_map, policies, desired)
        changed = changed or policy_changed
        results.append(result_policy)

        if not module.check_mode and result_policy:
            policies = [p for p in policies if p.get("_id") != result_policy.get("_id")]
            policies.append(result_policy)

    module.exit_json(changed=changed, policies=results, policy=results[0] if len(results) == 1 else None)


def apply_policy(module, api, site, zone_map, network_map, policies, desired):
    state = desired.get("state", "present")

    src_params = {"zone": "Internal", "matching_target": "ANY", "ips": [], "port": ""}
    src_params.update(desired.get("source") or {})

    dst_params = {"zone": "Internal", "matching_target": "ANY", "ips": [], "port": ""}
    dst_params.update(desired.get("destination") or {})

    src_zone_id = zone_map.get(src_params["zone"])
    dst_zone_id = zone_map.get(dst_params["zone"])

    if not src_zone_id or not dst_zone_id:
        module.fail_json(
            msg="Zone not found",
            name=desired["name"],
            src_zone=src_params["zone"],
            dst_zone=dst_params["zone"],
            available_zones=list(zone_map.keys()),
        )

    existing = None
    for policy in policies:
        if (
            policy.get("name") == desired["name"]
            and policy.get("source", {}).get("zone_id") == src_zone_id
            and policy.get("destination", {}).get("zone_id") == dst_zone_id
        ):
            existing = policy
            break

    desired_payload = {
        "name": desired["name"],
        "action": desired.get("action", "ALLOW"),
        "protocol": desired.get("protocol", "all"),
        "index": desired.get("index", 10000),
        "enabled": desired.get("enabled", True),
        "logging": desired.get("logging", False),
        "ip_version": "BOTH",
        "schedule": {"mode": "ALWAYS"},
        "connection_state_type": "ALL",
        "connection_states": [],
        "create_allow_respond": desired.get("action", "ALLOW") == "ALLOW",
        "icmp_typename": "ANY",
        "icmp_v6_typename": "ANY",
        "match_ip_sec": False,
        "match_opposite_protocol": False,
        "source": {
            "zone_id": src_zone_id,
            "matching_target": src_params["matching_target"],
            "match_opposite_ports": False,
            "port_matching_type": "SPECIFIC" if src_params["port"] else "ANY",
        },
        "destination": {
            "zone_id": dst_zone_id,
            "matching_target": dst_params["matching_target"],
            "match_opposite_ports": False,
            "port_matching_type": "SPECIFIC" if dst_params["port"] else "ANY",
        },
    }

    def resolve_network_ids(names):
        resolved = []
        for name in names:
            if name in network_map:
                resolved.append(network_map[name])
            else:
                module.fail_json(msg=f"Network '{name}' not found for firewall policy", name=desired["name"], network=name)
        return resolved

    if src_params["matching_target"] != "ANY":
        desired_payload["source"]["matching_target_type"] = "SPECIFIC"
        if src_params["matching_target"] == "NETWORK":
            desired_payload["source"]["network_ids"] = resolve_network_ids(src_params["ips"])
        else:
            desired_payload["source"]["ips"] = src_params["ips"]
    if dst_params["matching_target"] != "ANY":
        desired_payload["destination"]["matching_target_type"] = "SPECIFIC"
        if dst_params["matching_target"] == "NETWORK":
            desired_payload["destination"]["network_ids"] = resolve_network_ids(dst_params["ips"])
        else:
            desired_payload["destination"]["ips"] = dst_params["ips"]

    if src_params["port"]:
        desired_payload["source"]["port"] = src_params["port"]
    if dst_params["port"]:
        desired_payload["destination"]["port"] = dst_params["port"]

    if state == "present":
        if not existing:
            if module.check_mode:
                return True, desired_payload

            result_policy_res, info = api.request(
                f"/proxy/network/v2/api/site/{site}/firewall-policies", method="POST", data=desired_payload
            )
            if not result_policy_res:
                module.fail_json(msg="Failed to create policy", name=desired["name"], info=info)
            if isinstance(result_policy_res, dict) and "data" in result_policy_res:
                result_policy = result_policy_res["data"][0] if result_policy_res["data"] else {}
            else:
                result_policy = result_policy_res
            return True, result_policy

        changed = policy_needs_update(existing, desired_payload)
        if changed and not module.check_mode:
            result_policy_res, info = api.request(
                f"/proxy/network/v2/api/site/{site}/firewall-policies/{existing['_id']}",
                method="PUT",
                data=desired_payload,
            )
            if not result_policy_res:
                module.fail_json(msg="Failed to update policy", name=desired["name"], info=info)
            if isinstance(result_policy_res, dict) and "data" in result_policy_res:
                result_policy = result_policy_res["data"][0] if result_policy_res["data"] else {}
            else:
                result_policy = result_policy_res
            return True, result_policy
        return changed, existing

    if state == "absent" and existing:
        if not module.check_mode:
            _, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall-policies/{existing['_id']}", method="DELETE")
            if info["status"] not in [200, 204]:
                module.fail_json(msg="Failed to delete policy", name=desired["name"], info=info)
        return True, None

    return False, None


def policy_needs_update(existing, desired_payload):
    def match_field(side):
        target = side.get("matching_target")
        if target == "NETWORK":
            return "network_ids"
        if target == "IP":
            return "ips"
        if target == "DOMAIN":
            return "ips"
        return None

    for key in ["action", "protocol", "index", "enabled", "logging"]:
        if existing.get(key) != desired_payload[key]:
            return True

    src_field = match_field(desired_payload["source"])
    if src_field:
        if existing["source"].get(src_field) != desired_payload["source"].get(src_field):
            return True
    elif existing["source"].get("ips") or existing["source"].get("network_ids"):
        return True

    dst_field = match_field(desired_payload["destination"])
    if dst_field:
        if existing["destination"].get(dst_field) != desired_payload["destination"].get(dst_field):
            return True
    elif existing["destination"].get("ips") or existing["destination"].get("network_ids"):
        return True

    return (
        existing["source"].get("port", "") != desired_payload["source"].get("port", "")
        or existing["destination"].get("port", "") != desired_payload["destination"].get("port", "")
    )


if __name__ == "__main__":
    run_module()
