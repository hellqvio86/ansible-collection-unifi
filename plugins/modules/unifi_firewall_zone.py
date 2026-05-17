#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_firewall_zone
short_description: Manage UniFi v8.3+ Firewall Zones (Policy Engine)
version_added: "0.0.1"
description:
    - Create, update, or delete firewall zones in a UniFi controller using the modern Policy Engine.
    - This module targets the v2 API introduced in UniFi Network 8.x.
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
        description: Whether the firewall zone should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the firewall zone.
        required: false
        type: str
    type:
        description: Type of the firewall zone.
        choices: [ lan, wan, guest, iot, custom ]
        default: custom
        type: str
    description:
        description: Description of the firewall zone.
        type: str
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Create LAN firewall zone
  hellqvio86.unifi.unifi_firewall_zone:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: false
    name: "Internal"
    type: lan
    description: "Main LAN zone"
    state: present
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
        type=dict(type="str", choices=["lan", "wan", "guest", "iot", "custom"], default="custom"),
        description=dict(type="str"),
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

    # Fetch existing firewall zones via v2 API
    res, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall/zone")
    zones = api.as_list(res)
    if res is None:
        module.fail_json(msg="Failed to fetch firewall zones", info=info)

    existing = next((z for z in zones if z.get("name") == module.params["name"]), None)

    # Build payload
    desired_payload = {
        "name": module.params["name"],
        "type": module.params["type"].upper(),
        "description": module.params["description"] or "",
    }

    changed = False
    result_zone = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/v2/api/site/{site}/firewall/zone", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_zone = res_list[0] if res_list else res
                if not result_zone:
                    module.fail_json(msg="Failed to create firewall zone", info=info)
        else:
            # Normalize for comparison
            if (
                existing.get("name") != desired_payload["name"]
                or existing.get("type") != desired_payload["type"]
                or existing.get("description", "") != desired_payload["description"]
            ):
                changed = True

            if changed and not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/v2/api/site/{site}/firewall/zone/{existing['_id']}",
                    method="PUT",
                    data=desired_payload,
                )
                res_list = api.as_list(res)
                result_zone = res_list[0] if res_list else res
                if not result_zone:
                    module.fail_json(msg="Failed to update firewall zone", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(
                    f"/proxy/network/v2/api/site/{site}/firewall/zone/{existing['_id']}", method="DELETE"
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete firewall zone", info=info)
            result_zone = None

    module.exit_json(changed=changed, zone=result_zone)


if __name__ == "__main__":
    run_module()
