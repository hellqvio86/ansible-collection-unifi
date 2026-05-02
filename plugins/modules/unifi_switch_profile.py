#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_switch_profile
short_description: Manage UniFi Switch Profiles
version_added: "0.0.2"
description:
    - Create, update, or delete switch profiles in a UniFi controller.
    - Switch profiles define default port configurations for switches and can specify which port profiles to apply to which ports.
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
        description: Name of the switch profile.
        required: true
        type: str
    model:
        description: Switch model this profile applies to (e.g., USW-Flex, US-24, etc.).
        type: str
    port_profile_overrides:
        description: Dictionary mapping port numbers to port profile names.
        type: dict
        elements: str
    description:
        description: Optional description for the switch profile.
        type: str
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
        model=dict(type="str"),
        port_profile_overrides=dict(type="dict"),
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

    # 1. Fetch Port Profiles to resolve names to IDs
    port_profiles, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    if not port_profiles:
        module.fail_json(msg="Failed to fetch port profiles", info=info)

    port_profile_map = {p["name"]: p["_id"] for p in port_profiles}

    # 2. Resolve port profile overrides
    port_overrides = {}
    if module.params["port_profile_overrides"]:
        for port_num, profile_name in module.params["port_profile_overrides"].items():
            if profile_name not in port_profile_map:
                module.fail_json(msg=f"Port profile '{profile_name}' not found")
            port_overrides[int(port_num)] = port_profile_map[profile_name]

    # 3. Fetch existing switch profiles
    switch_profiles, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile")
    if switch_profiles is None:
        module.fail_json(msg="Failed to fetch switch profiles", info=info)

    existing = next((p for p in switch_profiles if p.get("name") == module.params["name"]), None)

    # 4. Build Desired Payload
    desired_payload = {"name": module.params["name"]}
    if module.params["model"]:
        desired_payload["model"] = module.params["model"]
    if port_overrides:
        desired_payload["port_overrides"] = port_overrides
    if module.params["description"]:
        desired_payload["description"] = module.params["description"]

    changed = False
    result_profile = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                result_profile, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/switchprofile", method="POST", data=desired_payload
                )
                if not result_profile:
                    module.fail_json(msg="Failed to create switch profile", info=info)
        else:
            # Compare and update
            for key, value in desired_payload.items():
                if existing.get(key) != value:
                    changed = True
                    break

            if changed and not module.check_mode:
                result_profile, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}", method="PUT", data=desired_payload
                )
                if not result_profile:
                    module.fail_json(msg="Failed to update switch profile", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}", method="DELETE")
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete switch profile", info=info)
            result_profile = None

    module.exit_json(changed=changed, profile=result_profile)


if __name__ == "__main__":
    run_module()