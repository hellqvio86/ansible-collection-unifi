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
    site:
        description: UniFi site name.
        type: str
        default: default
    validate_certs:
        description: Verify SSL certificates.
        type: bool
        default: true
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
    unifi_session_cookie:
        description: Pre-authenticated session cookie string.
        type: str
        required: false
    unifi_csrf_token:
        description: Pre-authenticated CSRF token.
        type: str
        required: false
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

EXAMPLES = r"""
- name: Register admin keys
  hellqvio86.unifi.unifi_ssh_key:
    keys:
      - "ssh-rsa AAAAB3Nza..."
      - "ssh-ed25519 AAAAC3Nza..."
"""

RETURN = r"""
ssh_keys:
    description: Registered SSH keys on the controller.
    type: list
    returned: always
"""

import base64
import datetime
import hashlib

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def _parse_ssh_key(key_str: str) -> dict:
    parts = key_str.strip().split()
    if len(parts) < 2:
        return {}
    k_type = parts[0]
    k_b64 = parts[1]
    k_comment = parts[2] if len(parts) > 2 else ""
    name = k_comment.split("@")[-1] if "@" in k_comment else (k_comment or "ssh-key")
    try:
        raw = base64.b64decode(k_b64)
        md5 = hashlib.md5(raw).hexdigest()  # noqa: S324 - UniFi MD5 fingerprint format
        fp = ":".join(md5[i : i + 2] for i in range(0, 32, 2))
    except Exception:
        fp = ""

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "name": name,
        "type": k_type,
        "key": k_b64,
        "comment": k_comment,
        "fingerprint": fp,
        "date": now_iso,
    }


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
        keys=dict(type="list", elements="str", required=False, default=[], no_log=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    site = module.params.get("site", "default")
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

    # 2. Check if legacy /api/users/self provides sshKeys
    user_info, info = api.request("/api/users/self")
    if user_info and "sshKeys" in user_info:
        current_keys = user_info.get("sshKeys", [])
        new_key_list = current_keys
        changed = False

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
            res, patch_info = api.request("/api/users/self", method="PATCH", data={"sshKeys": new_key_list})
            if patch_info.get("status") != 200:
                module.fail_json(msg="Failed to update SSH keys", info=patch_info)

        module.exit_json(changed=changed, keys_count=len(new_key_list))
        return

    # 3. UniFi Network controller setting/mgmt endpoint
    mgmt_res, mgmt_info = api.request(f"/proxy/network/api/s/{site}/get/setting/mgmt")
    mgmt_list = api.as_list(mgmt_res) if mgmt_res else []
    mgmt = mgmt_list[0] if mgmt_list and isinstance(mgmt_list[0], dict) else None
    if not mgmt or "_id" not in mgmt:
        module.fail_json(msg="Failed to fetch management settings for SSH keys", info=mgmt_info)

    existing_keys = mgmt.get("x_ssh_keys", [])
    existing_keys_b64 = {k.get("key") for k in existing_keys if isinstance(k, dict) and k.get("key")}

    parsed_desired = [_parse_ssh_key(k) for k in desired_keys if k and _parse_ssh_key(k).get("key")]
    desired_b64 = {p["key"] for p in parsed_desired if p.get("key")}

    changed = False
    new_keys = list(existing_keys)

    if state == "present":
        for p in parsed_desired:
            if p["key"] not in existing_keys_b64:
                changed = True
                new_keys.append(p)
                existing_keys_b64.add(p["key"])
    elif state == "absent":
        to_remove = existing_keys_b64.intersection(desired_b64)
        if to_remove:
            changed = True
            new_keys = [k for k in existing_keys if isinstance(k, dict) and k.get("key") not in to_remove]

    if changed and not module.check_mode:
        payload = dict(mgmt)
        payload["x_ssh_keys"] = new_keys
        res, put_info = api.request(
            f"/proxy/network/api/s/{site}/set/setting/mgmt/{mgmt['_id']}",
            method="PUT",
            data=payload,
        )
        if put_info.get("status") != 200:
            module.fail_json(msg="Failed to update SSH keys in setting/mgmt", info=put_info)

    module.exit_json(changed=changed, keys_count=len(new_keys))


if __name__ == "__main__":
    run_module()
