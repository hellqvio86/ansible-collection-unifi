#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_wlan
short_description: Manage UniFi wireless network (WLAN) configurations
version_added: "0.0.1"
description:
    - Create, update, or delete UniFi WLAN configurations.
    - This module manages the controller's wireless network definitions in the configured site.
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
        description: Whether the WLAN should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the wireless network (SSID).
        required: true
        type: str
    enabled:
        description: Enable or disable the WLAN.
        type: bool
    network_name:
        description: Name of the associated network profile.
        type: str
    security:
        description: Security mode for the WLAN.
        choices: [ open, wpapsk, wpa2, wpa3 ]
        type: str
    passphrase:
        description: WPA passphrase for secured networks.
        type: str
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Ensure guest SSID exists
  hellqvio86.unifi.unifi_wlan:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: false
    name: "Guest WLAN"
    enabled: true
    network_name: "Guest"
    security: wpapsk
    passphrase: "supersecret"
    state: present
"""

RETURN = r"""
wlan:
    description: The created or updated WLAN configuration object.
    type: dict
    returned: when state is present
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
        enabled=dict(type="bool"),
        network_name=dict(type="str"),
        security=dict(type="str", choices=["open", "wpapsk", "wpa2", "wpa3"]),
        passphrase=dict(type="str", no_log=True),
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

    # Fetch existing WLAN configs
    wlans_res, info = api.request(f"/proxy/network/api/s/{site}/rest/wlanconf")
    wlans = api.as_list(wlans_res)
    if wlans_res is None:
        module.fail_json(msg="Failed to fetch WLAN configurations", info=info)

    existing = next((w for w in wlans if isinstance(w, dict) and w.get("name") == module.params["name"]), None)

    # Build payload from provided parameters
    desired_payload = {"name": module.params["name"]}
    if module.params["enabled"] is not None:
        desired_payload["enabled"] = module.params["enabled"]
    if module.params["network_name"]:
        # Resolve network name to ID if possible
        networks_res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
        networks = api.as_list(networks_res)
        network = next(
            (n for n in networks if isinstance(n, dict) and n.get("name") == module.params["network_name"]), None
        )
        if network:
            desired_payload["networkconf_id"] = network["_id"]
        else:
            module.fail_json(msg=f"Network '{module.params['network_name']}' not found")

    if module.params["security"]:
        desired_payload["security"] = module.params["security"]
    if module.params["passphrase"]:
        desired_payload["x_passphrase"] = module.params["passphrase"]

    changed = False
    result_wlan = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/wlanconf", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_wlan = res_list[0] if res_list else res
                if not result_wlan:
                    module.fail_json(msg="Failed to create WLAN configuration", info=info)
        else:
            for key, value in desired_payload.items():
                if existing.get(key) != value:
                    changed = True
                    break

            if changed and not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/wlanconf/{existing['_id']}", method="PUT", data=desired_payload
                )
                res_list = api.as_list(res)
                result_wlan = res_list[0] if res_list else res
                if not result_wlan:
                    module.fail_json(msg="Failed to update WLAN configuration", info=info)

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(f"/proxy/network/api/s/{site}/rest/wlanconf/{existing['_id']}", method="DELETE")
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete WLAN configuration", info=info)
            result_wlan = None

    module.exit_json(changed=changed, wlan=result_wlan)


if __name__ == "__main__":
    run_module()
