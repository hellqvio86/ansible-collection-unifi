#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_port_profile
short_description: Manage UniFi Port Profiles (Port Configurations)
version_added: "0.0.1"
description:
    - Create, update, or delete port profiles in a UniFi controller.
    - These profiles define settings like native VLAN, tagged VLANs, PoE, and speed for switch ports.
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
        description: Whether the profile should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the port profile.
        required: true
        type: str
    native_network_name:
        description: Name of the native (untagged) network.
        type: str
    tagged_network_names:
        description: List of names of tagged networks.
        type: list
        elements: str
    poe_mode:
        description: PoE mode for the port.
        choices: [ auto, off, passthrough ]
        type: str
    isolation:
        description: Enable port isolation.
        type: bool
    autoneg:
        description: Enable auto-negotiation.
        type: bool
        default: true
author:
    - hellqvio86 (@hellqvio86)
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
        native_network_name=dict(type="str"),
        tagged_network_names=dict(type="list", elements="str"),
        poe_mode=dict(type="str", choices=["auto", "off", "passthrough"]),
        isolation=dict(type="bool"),
        autoneg=dict(type="bool", default=True),
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

    # 1. Fetch Networks to resolve names to IDs
    networks, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    if not networks:
        module.fail_json(msg="Failed to fetch networks", info=info)

    network_map = {n["name"]: n["_id"] for n in networks}

    # 2. Resolve Native Network ID
    native_id = None
    if module.params["native_network_name"]:
        native_id = network_map.get(module.params["native_network_name"])
        if not native_id:
            module.fail_json(msg=f"Native network '{module.params['native_network_name']}' not found")

    # 3. Resolve Tagged Network IDs
    tagged_ids = []
    if module.params["tagged_network_names"]:
        for name in module.params["tagged_network_names"]:
            tid = network_map.get(name)
            if not tid:
                module.fail_json(msg=f"Tagged network '{name}' not found")
            tagged_ids.append(tid)

    # 4. Fetch Port Profiles
    profiles, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    if profiles is None:
        module.fail_json(msg="Failed to fetch port profiles", info=info)

    existing = next((p for p in profiles if p.get("name") == module.params["name"]), None)

    # 5. Build Desired Payload
    desired_payload = {"name": module.params["name"], "autoneg": module.params["autoneg"]}
    if native_id:
        desired_payload["native_networkconf_id"] = native_id
    if tagged_ids:
        desired_payload["tagged_networkconf_ids"] = tagged_ids
    if module.params["poe_mode"]:
        desired_payload["poe_mode"] = module.params["poe_mode"]
    if module.params["isolation"] is not None:
        desired_payload["isolation"] = module.params["isolation"]

    changed = False
    result_profile = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                result_profile, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf", method="POST", data=desired_payload
                )
                if not result_profile:
                    module.fail_json(msg="Failed to create port profile", info=info)
        else:
            # Compare and update
            for key, value in desired_payload.items():
                if existing.get(key) != value:
                    changed = True
                    break

            if changed and not module.check_mode:
                result_profile, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="PUT", data=desired_payload
                )
                if not result_profile:
                    module.fail_json(msg="Failed to update port profile", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="DELETE")
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete port profile", info=info)
            result_profile = None

    module.exit_json(changed=changed, profile=result_profile)


if __name__ == "__main__":
    run_module()
