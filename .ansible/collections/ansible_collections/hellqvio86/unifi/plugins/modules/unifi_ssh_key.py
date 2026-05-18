#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


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
        default: false
        type: bool
    keys:
        description: List of SSH public keys to ensure are present.
        required: false
        type: list
        elements: str
    state:
        description: Whether the keys should be present or absent.
        choices: [ present ]
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
        validate_certs=dict(type="bool", default=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        keys=dict(type="list", elements="str", required=False),
        state=dict(type="str", choices=["present"], default="present"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    validate_certs = module.params["validate_certs"]
    desired_keys = module.params["keys"]

    # 1. Initialize API and Login
    api = UnifiAPI(
        module,
        host,
        username,
        password,
        validate_certs,
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
    )
    api.login()

    # 2. Get current user settings (contains sshKeys)
    user_info, info = api.request("/api/users/self")
    if not user_info:
        module.fail_json(msg="Failed to fetch user info", info=info)

    current_keys = user_info.get("sshKeys", [])

    # 3. Check for differences
    # We want to ensure all desired_keys are in current_keys
    missing_keys = [k for k in desired_keys if k not in current_keys]

    changed = False
    if missing_keys:
        changed = True
        new_key_list = list(set(current_keys + desired_keys))

        if not module.check_mode:
            # Update via PATCH /api/users/self
            res, info = api.request("/api/users/self", method="PATCH", data={"sshKeys": new_key_list})
            if info["status"] != 200:
                module.fail_json(msg="Failed to update SSH keys", info=info)

    module.exit_json(changed=changed, keys_count=len(current_keys if not changed else new_key_list))


if __name__ == "__main__":
    run_module()
