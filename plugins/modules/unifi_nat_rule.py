#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_nat_rule
short_description: Manage UniFi Source NAT / Masquerade rules via the controller API
description:
  - Creates, updates, or deletes Source NAT (SNAT) or Masquerade rules on a UniFi
    controller using the C(/proxy/network/v2/api/site/{site}/firewall/nat) endpoint.
  - Rules are matched by name for idempotency; an existing rule with the same name
    is updated in-place rather than duplicated.
  - This module never uses SSH or direct iptables; all changes go through the HTTP API.
options:
  host:
    description: Hostname or IP address of the UniFi controller.
    type: str
  username:
    description: Controller admin username.
    type: str
    no_log: true
  password:
    description: Controller admin password.
    type: str
    no_log: true
  site:
    description: UniFi site name.
    type: str
    default: default
  validate_certs:
    description: Validate TLS certificates on the controller.
    type: bool
    default: true
  ca_path:
    description: Path to CA bundle file for TLS verification.
    type: path
    required: false
  unifi_session_cookie:
    description: Pre-authenticated session cookie (skips login step).
    type: str
    no_log: true
    required: false
  unifi_csrf_token:
    description: Pre-authenticated CSRF token (skips login step).
    type: str
    no_log: true
    required: false
  state:
    description: Whether the rule should exist.
    choices: [present, absent]
    default: present
    type: str
  name:
    description:
      - Human-readable name for the rule.
      - Used as the idempotency key — the module matches rules by this name.
    required: true
    type: str
  type:
    description:
      - NAT rule type.
      - C(masquerade) hides the source behind the outbound interface IP (many-to-one).
      - C(source) translates to a specific address set in C(translated_src).
    choices: [masquerade, source]
    default: masquerade
    type: str
  src_address:
    description:
      - Source IP or CIDR to match before translation (e.g. C(192.0.2.10) or C(192.0.2.0/24)).
    type: str
    required: true
  dst_address:
    description:
      - Destination IP or CIDR to match (e.g. C(198.51.100.0/24)).
      - Leave empty to match any destination.
    type: str
    default: ""
  outbound_interface:
    description:
      - UniFi network name whose interface is used as the post-NAT egress interface.
      - The module resolves the human-readable name to the internal C(_id) via
        C(/proxy/network/api/s/{site}/rest/networkconf).
      - Required for C(masquerade); optional for C(source).
    type: str
    default: ""
  translated_src:
    description:
      - For C(type=source) — the specific IP to translate the source address to.
      - Not used for C(masquerade).
    type: str
    default: ""
  enabled:
    description: Whether the rule is active.
    type: bool
    default: true
  logging:
    description: Whether to log packets matching this rule.
    type: bool
    default: false
author:
  - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Masquerade Home Assistant traffic to Generic IoT subnet
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Generic IoT"
    type: masquerade
    src_address: "192.0.2.10"
    dst_address: "198.51.100.0/24"
    outbound_interface: "LAN_IoT"
    enabled: true

- name: Source-NAT to a specific translated address
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT gateway traffic"
    type: source
    src_address: "198.51.100.0/24"
    dst_address: ""
    translated_src: "203.0.113.5"
    enabled: true

- name: Remove a NAT rule
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Generic IoT"
    src_address: "192.0.2.10"
    state: absent
"""

RETURN = r"""
changed:
    description: Whether a change was applied to the controller.
    type: bool
    returned: always
rule:
    description: Current state of the NAT rule after the operation, or null if deleted.
    type: dict
    returned: always
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

_NAT_PATH = "/proxy/network/v2/api/site/{site}/firewall/nat"
_NETCONF_PATH = "/proxy/network/api/s/{site}/rest/networkconf"


def _resolve_network_id(api: UnifiAPI, site: str, name: str) -> str:
    """Resolve a UniFi network name to its internal _id string."""
    if not name:
        return ""
    res, info = api.request(_NETCONF_PATH.format(site=site))
    if info["status"] != 200:
        api.module.fail_json(msg="Failed to fetch networkconf", info=info)
    networks = api.as_list(res)
    match = next(
        (n for n in networks if isinstance(n, dict) and n.get("name") == name),
        None,
    )
    if match is None:
        api.module.fail_json(msg=f"Network '{name}' not found in networkconf — check the outbound_interface value")
    return str(match["_id"])


def _build_desired(
    name: str,
    rule_type: str,
    src_address: str,
    dst_address: str,
    outbound_network_id: str,
    translated_src: str,
    enabled: bool,
    logging: bool,
) -> dict[str, Any]:
    """Build the desired NAT rule payload."""
    payload: dict[str, Any] = {
        "name": name,
        "type": rule_type,
        "src_address": src_address,
        "dst_address": dst_address,
        "enabled": enabled,
        "logging": logging,
    }
    if outbound_network_id:
        payload["outbound_network_id"] = outbound_network_id
    if translated_src:
        payload["translated_src"] = translated_src
    return payload


def _rules_differ(current: dict[str, Any], desired: dict[str, Any]) -> bool:
    """Return True if any key in desired differs from current (ignoring _id)."""
    for key, val in desired.items():
        if key == "_id":
            continue
        if current.get(key) != val:
            return True
    return False


def _find_rule(module: AnsibleModule, rules: list[Any], name: str) -> dict[str, Any] | None:
    """Return the rule dict whose name matches, failing if multiple rules match."""
    matches = [r for r in rules if isinstance(r, dict) and r.get("name") == name]
    if len(matches) > 1:
        module.fail_json(msg=f"Ambiguous resource: multiple NAT rules match name '{name}'")
    return matches[0] if matches else None


def run_module() -> None:
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        type=dict(type="str", choices=["masquerade", "source"], default="masquerade"),
        src_address=dict(type="str", required=True),
        dst_address=dict(type="str", default=""),
        outbound_interface=dict(type="str", default=""),
        translated_src=dict(type="str", default=""),
        enabled=dict(type="bool", default=True),
        logging=dict(type="bool", default=False),
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
        ca_path=module.params.get("ca_path"),
    )
    api.login()

    site: str = module.params["site"]
    name: str = module.params["name"]
    state: str = module.params["state"]
    nat_path: str = _NAT_PATH.format(site=site)

    outbound_network_id = _resolve_network_id(api, site, module.params["outbound_interface"])

    res, info = api.request(nat_path)
    if info["status"] not in [200, 204]:
        module.fail_json(msg="Failed to fetch NAT rules", info=info)

    current = _find_rule(module, api.as_list(res), name)

    # --- absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, rule=None)
            return
        if not module.check_mode:
            _, del_info = api.request(f"{nat_path}/{current['_id']}", method="DELETE")
            if del_info["status"] not in [200, 204]:
                module.fail_json(msg="Failed to delete NAT rule", info=del_info, name=name)
                return
        module.exit_json(changed=True, rule=None)
        return

    # --- present ---
    desired = _build_desired(
        name=name,
        rule_type=module.params["type"],
        src_address=module.params["src_address"],
        dst_address=module.params["dst_address"],
        outbound_network_id=outbound_network_id,
        translated_src=module.params["translated_src"],
        enabled=module.params["enabled"],
        logging=module.params["logging"],
    )

    if current is not None:
        if not _rules_differ(current, desired):
            module.exit_json(changed=False, rule=current)
            return
        if not module.check_mode:
            payload = {**current, **desired}
            res, upd_info = api.request(f"{nat_path}/{current['_id']}", method="PUT", data=payload)
            if upd_info["status"] not in [200, 201]:
                module.fail_json(msg="Failed to update NAT rule", info=upd_info, name=name)
                return
            updated = api.as_list(res)
            current = updated[0] if updated else payload
        module.exit_json(changed=True, rule=current)
        return

    # create
    if not module.check_mode:
        res, crt_info = api.request(nat_path, method="POST", data=desired)
        if crt_info["status"] not in [200, 201]:
            module.fail_json(msg="Failed to create NAT rule", info=crt_info, name=name)
            return
        created = api.as_list(res)
        current = created[0] if created else desired
    module.exit_json(changed=True, rule=current)


if __name__ == "__main__":
    run_module()
