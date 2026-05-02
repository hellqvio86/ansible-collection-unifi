#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_firewall_zone
short_description: Manage UniFi firewall zones (firewall groups)
version_added: "0.0.1"
description:
    - Create, update, or delete UniFi firewall zones (firewall groups).
    - Firewall zones are used to group interfaces and apply firewall rules between zones.
    - Following Ubiquiti best practices, create zones for each VLAN to enable proper network segmentation.
options:
    host:
        description: The host of the UniFi controller.
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
        required: true
        type: str
    type:
        description: Type of the firewall zone.
        choices: [ lan, wan, guest, iot, custom ]
        default: lan
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
    host: "192.168.60.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: false
    name: "LAN"
    type: lan
    description: "Local Area Network zone"
    state: present

- name: Create IoT firewall zone for VLAN isolation
  hellqvio86.unifi.unifi_firewall_zone:
    host: "192.168.60.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: false
    name: "IoT"
    type: iot
    description: "IoT devices VLAN zone"
    state: present
"""

RETURN = r"""
zone:
    description: The created or updated firewall zone object.
    type: dict
    returned: when state is present
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module_args = dict(
        host=dict(type="str", required=True),
        username=dict(type="str", required=True, no_log=True),
        password=dict(type="str", required=True, no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        type=dict(type="str", choices=["lan", "wan", "guest", "iot", "custom"], default="lan"),
        description=dict(type="str"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    api = UnifiAPI(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"],
        module.params["validate_certs"],
    )
    api.login()

    site = module.params["site"]

    # Fetch existing firewall zones
    zones, info = api.request(f"/proxy/network/api/s/{site}/rest/firewallgroup")
    if zones is None:
        module.fail_json(msg="Failed to fetch firewall zones", info=info)

    existing = next((z for z in zones if z.get("name") == module.params["name"]), None)

    # Build payload
    desired_payload = {"name": module.params["name"], "type": module.params["type"]}
    if module.params["description"]:
        desired_payload["description"] = module.params["description"]

    changed = False
    result_zone = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                result_zone, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/firewallgroup", method="POST", data=desired_payload
                )
                if not result_zone:
                    module.fail_json(msg="Failed to create firewall zone", info=info)
        else:
            for key, value in desired_payload.items():
                if existing.get(key) != value:
                    changed = True
                    break

            if changed and not module.check_mode:
                result_zone, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/firewallgroup/{existing['_id']}", method="PUT", data=desired_payload
                )
                if not result_zone:
                    module.fail_json(msg="Failed to update firewall zone", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/firewallgroup/{existing['_id']}", method="DELETE"
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete firewall zone", info=info)
            result_zone = None

    module.exit_json(changed=changed, zone=result_zone)


if __name__ == "__main__":
    run_module()