#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_port_profile
short_description: Manage UniFi switch port profiles
version_added: "0.0.1"
description:
    - Create, update, or delete port profiles in a UniFi controller.
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
        description: Whether the profile should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the port profile.
        required: false
        type: str
    native_network_name:
        description: Name of the native (untagged) network.
        type: str
    tagged_network_names:
        description: List of names of tagged networks.
        type: list
        elements: str
    autoneg:
        description: Whether to enable auto-negotiation.
        type: bool
author:
    - hellqvio86 (@hellqvio86)
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
        native_network_name=dict(type="str"),
        tagged_network_names=dict(type="list", elements="str"),
        autoneg=dict(type="bool"),
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

    # Fetch existing port profiles
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    profiles = api.as_list(res)
    if res is None:
        module.fail_json(msg="Failed to fetch port profiles", info=info)

    existing = next((p for p in profiles if p.get("name") == module.params["name"]), None)

    # Fetch networks once for resolution
    networks_res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    networks = api.as_list(networks_res)
    network_map = {n["name"]: n["_id"] for n in networks if isinstance(n, dict)}

    # Build payload
    desired_payload = {"name": module.params["name"]}
    if module.params["native_network_name"]:
        nn_id = network_map.get(module.params["native_network_name"])
        if not nn_id:
            module.fail_json(msg=f"Native network '{module.params['native_network_name']}' not found")
        desired_payload["native_networkconf_id"] = nn_id

    if module.params["tagged_network_names"] is not None:
        tn_ids = []
        for name in module.params["tagged_network_names"]:
            tn_id = network_map.get(name)
            if not tn_id:
                module.fail_json(msg=f"Tagged network '{name}' not found")
            tn_ids.append(tn_id)
        desired_payload["tagged_networkconf_ids"] = tn_ids

    if module.params["autoneg"] is not None:
        desired_payload["autoneg"] = module.params["autoneg"]

    changed = False
    result_profile = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_profile = res_list[0] if res_list else res
                if not result_profile:
                    module.fail_json(msg="Failed to create port profile", info=info)
        else:
            for key, value in desired_payload.items():
                if existing.get(key) != value:
                    changed = True
                    break

            if changed and not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="PUT", data=desired_payload
                )
                res_list = api.as_list(res)
                result_profile = res_list[0] if res_list else res
                if not result_profile:
                    module.fail_json(msg="Failed to update port profile", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="DELETE"
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete port profile", info=info)
            result_profile = None

    module.exit_json(changed=changed, profile=result_profile)


if __name__ == "__main__":
    run_module()
