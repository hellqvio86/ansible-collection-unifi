#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_switch_profile
short_description: Manage UniFi switch profiles (logical groups of port overrides)
version_added: "0.0.1"
description:
    - Manage UniFi switch profiles which define a set of port-level overrides for specific switch models.
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
        description: Name of the switch profile.
        required: false
        type: str
    model:
        description: Switch model this profile applies to (e.g., USMINI).
        required: false
        type: str
    description:
        description: Description of the switch profile.
        type: str
    port_profile_overrides:
        description: Dictionary mapping port numbers to port profile names.
        type: dict
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Create a switch profile with port overrides
  hellqvio86.unifi.unifi_switch_profile:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Standard-24-Port"
    model: "USL24P"
    description: "Switch profile for 24-port switch"
    port_profile_overrides:
      "1": "Trunk-Profile"
      "12": "Trunk-Profile"
      "2": "IoT-Profile"
    state: present
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def _build_desired_payload(module):
    payload = {
        "name": module.params["name"],
    }
    if module.params.get("model") is not None:
        payload["model"] = module.params["model"]
    if module.params.get("description") is not None:
        payload["description"] = module.params["description"]
    if module.params.get("port_profile_overrides") is not None:
        payload["port_profile_overrides"] = module.params["port_profile_overrides"]
    return payload


def _needs_update(existing, desired):
    for key in ("model", "description", "port_profile_overrides"):
        if key in desired and existing.get(key) != desired[key]:
            return True
    return False


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
        model=dict(type="str", required=False),
        description=dict(type="str"),
        port_profile_overrides=dict(type="dict"),
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

    # Fetch existing switch profiles
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile")
    if info.get("status") != 200:
        module.exit_json(
            changed=False,
            switchprofile_api_supported=False,
            msg="Switch profile API unsupported on this controller; skipped.",
        )
    profiles = api.as_list(res)

    existing = next((p for p in profiles if p.get("name") == name), None)

    changed = False
    result_profile = existing

    desired_payload = _build_desired_payload(module)

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/switchprofile", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_profile = res_list[0] if res_list else res
                if not result_profile:
                    module.fail_json(msg="Failed to create switch profile", info=info)
        else:
            if _needs_update(existing, desired_payload):
                changed = True
                if not module.check_mode:
                    res, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}",
                        method="PUT",
                        data=desired_payload,
                    )
                    res_list = api.as_list(res)
                    result_profile = res_list[0] if res_list else res
                    if not result_profile:
                        module.fail_json(msg="Failed to update switch profile", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}", method="DELETE"
                )
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete switch profile", info=info)
            result_profile = None

    module.exit_json(changed=changed, profile=result_profile)


if __name__ == "__main__":
    run_module()
