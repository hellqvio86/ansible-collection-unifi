#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)


DOCUMENTATION = r"""
---
module: unifi_ssh_key
short_description: Manage persistent SSH keys on UniFi OS
version_added: "0.0.1"
description:
    - Registers SSH public keys in the UniFi OS system configuration.
    - Unlike authorized_keys, these keys persist across reboots and provisions.
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
    validate_certs:
        description: Verify SSL certificates.
        default: true
        type: bool
    api_key:
        description:
            - Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+).
            - Preferred over username/password.
            - Can also be set via the C(UNIFI_API_KEY) or C(UNIFI_API_TOKEN) environment variables.
        type: str
        required: false
    ca_path:
        description: Path to CA bundle file for TLS verification.
        required: false
        type: path
    keys:
        description: List of SSH public keys to ensure are present or absent.
        required: false
        type: list
        elements: str
        default: []
    state:
        description: Whether the keys should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
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
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        keys=dict(type="list", elements="str", required=False, default=[]),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    validate_certs = module.params["validate_certs"]
    desired_keys = module.params.get("keys") or []
    state = module.params["state"]

    # 1. Initialize API and Login
    api = UnifiAPI(
        module,
        host,
        username,
        password,
        validate_certs,
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    # 2. Get current user settings (contains sshKeys)
    user_info, info = api.request("/api/users/self")
    if not user_info:
        module.fail_json(msg="Failed to fetch user info", info=info)

    current_keys = user_info.get("sshKeys", [])
    new_key_list = current_keys
    changed = False

    # 3. Check for differences and update deterministically
    if state == "present":
        missing_keys = [k for k in desired_keys if k not in current_keys]
        if missing_keys:
            changed = True
            new_key_list = list(dict.fromkeys(current_keys + desired_keys))
    elif state == "absent":
        keys_to_remove = [k for k in desired_keys if k in current_keys]
        if keys_to_remove:
            changed = True
            new_key_list = [k for k in current_keys if k not in desired_keys]

    if changed and not module.check_mode:
        # Update via PATCH /api/users/self
        res, info = api.request("/api/users/self", method="PATCH", data={"sshKeys": new_key_list})
        if info["status"] != 200:
            module.fail_json(msg="Failed to update SSH keys", info=info)

    module.exit_json(changed=changed, keys_count=len(new_key_list))


if __name__ == "__main__":
    run_module()
