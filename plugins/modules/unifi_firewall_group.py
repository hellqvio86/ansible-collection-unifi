#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_firewall_group
short_description: Manage UniFi firewall groups (address or port groups)
version_added: "0.0.1"
description:
    - Create, update, or delete firewall groups in a UniFi controller.
    - Supports both address-group (IPs/Networks) and port-group (Ports).
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
        description: Whether the group should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the firewall group.
        required: false
        type: str
    group_type:
        description: Type of the group.
        choices: [ address-group, port-group ]
        default: address-group
        type: str
    group_members:
        description: List of members (IPs, networks, or ports).
        type: list
        elements: str
        required: false
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Ensure web ports group exists
  hellqvio86.unifi.unifi_firewall_group:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Web Ports"
    group_type: "port-group"
    group_members: ["80", "443"]

- name: Ensure internal networks group exists
  hellqvio86.unifi.unifi_firewall_group:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Internal Networks"
    group_type: "address-group"
    group_members: ["192.0.2.0/24", "198.51.100.0/24"]
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
        group_type=dict(type="str", choices=["address-group", "port-group"], default="address-group"),
        group_members=dict(type="list", elements="str", required=False),
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
    group_type = module.params["group_type"]
    group_members = module.params["group_members"]

    # Fetch existing groups
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/firewallgroup")
    groups = api.as_list(res)

    existing = next((g for g in groups if g.get("name") == name), None)

    changed = False
    result_group = existing

    desired_payload = {
        "name": name,
        "group_type": group_type,
        "group_members": group_members,
    }

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/firewallgroup", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_group = res_list[0] if res_list else res
                if not result_group:
                    module.fail_json(msg="Failed to create firewall group", info=info)
        else:
            # Check if group type matches (usually cannot change type after creation without recreate)
            if existing.get("group_type") != group_type:
                module.fail_json(msg=f"Group '{name}' already exists with different type '{existing.get('group_type')}'")

            # Check if members match
            if sorted(existing.get("group_members", [])) != sorted(group_members):
                changed = True
                if not module.check_mode:
                    res, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/firewallgroup/{existing['_id']}",
                        method="PUT",
                        data=desired_payload
                    )
                    res_list = api.as_list(res)
                    result_group = res_list[0] if res_list else res
                    if not result_group:
                        module.fail_json(msg="Failed to update firewall group", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/firewallgroup/{existing['_id']}", method="DELETE"
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete firewall group", info=info)
            result_group = None

    module.exit_json(changed=changed, group=result_group)


if __name__ == "__main__":
    run_module()
