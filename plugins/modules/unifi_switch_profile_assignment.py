#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_switch_profile_assignment
short_description: Assign Switch Profiles to UniFi Switches
version_added: "0.0.2"
description:
    - Assign or remove switch profiles from UniFi switches.
    - This allows you to apply predefined port configurations to switches.
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
        description: Whether the profile assignment should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    switch_name:
        description: Name of the switch to assign the profile to.
        type: str
    switch_mac:
        description: MAC address of the switch to assign the profile to.
        type: str
    switch_ip:
        description: IP address of the switch to assign the profile to.
        type: str
    profile_name:
        description: Name of the switch profile to assign.
        required: true
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
        switch_name=dict(type="str"),
        switch_mac=dict(type="str"),
        switch_ip=dict(type="str"),
        profile_name=dict(type="str", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Validate that at least one switch identifier is provided
    switch_identifiers = [module.params["switch_name"], module.params["switch_mac"], module.params["switch_ip"]]
    if not any(switch_identifiers):
        module.fail_json(msg="At least one of switch_name, switch_mac, or switch_ip must be provided")

    api = UnifiAPI(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"],
        module.params["validate_certs"],
    )
    api.login()

    site = module.params["site"]

    # 1. Fetch Switch Profiles to resolve name to ID
    switch_profiles, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile")
    if switch_profiles is None:
        module.fail_json(msg="Failed to fetch switch profiles", info=info)

    profile_map = {p["name"]: p["_id"] for p in switch_profiles}
    if module.params["profile_name"] not in profile_map:
        module.fail_json(msg=f"Switch profile '{module.params['profile_name']}' not found")
    profile_id = profile_map[module.params["profile_name"]]

    # 2. Fetch Devices to find the target switch
    devices, info = api.request(f"/proxy/network/api/s/{site}/rest/device")
    if devices is None:
        module.fail_json(msg="Failed to fetch devices", info=info)

    # Find the target switch
    target_switch = None
    for device in devices:
        if device.get("type") != "usw":  # Only look at switches
            continue

        # Check if this device matches any of the provided identifiers
        matches = False
        if module.params["switch_name"] and device.get("name") == module.params["switch_name"]:
            matches = True
        elif module.params["switch_mac"] and device.get("mac") == module.params["switch_mac"]:
            matches = True
        elif module.params["switch_ip"] and device.get("ip") == module.params["switch_ip"]:
            matches = True

        if matches:
            target_switch = device
            break

    if not target_switch:
        module.fail_json(msg="Switch not found with provided identifiers")

    switch_id = target_switch["_id"]
    current_profile_id = target_switch.get("switch_profile_id")

    changed = False

    if module.params["state"] == "present":
        if current_profile_id != profile_id:
            changed = True
            if not module.check_mode:
                update_payload = {"switch_profile_id": profile_id}
                result, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/device/{switch_id}", method="PUT", data=update_payload
                )
                if not result:
                    module.fail_json(msg="Failed to assign switch profile", info=info)
                target_switch = result

    elif module.params["state"] == "absent":
        if current_profile_id is not None:
            changed = True
            if not module.check_mode:
                update_payload = {"switch_profile_id": None}
                result, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/device/{switch_id}", method="PUT", data=update_payload
                )
                if not result:
                    module.fail_json(msg="Failed to remove switch profile assignment", info=info)
                target_switch = result

    module.exit_json(changed=changed, switch=target_switch)


if __name__ == "__main__":
    run_module()