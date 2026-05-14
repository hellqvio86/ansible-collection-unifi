#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_rsyslog
short_description: Manage UniFi Remote Syslog (rsyslogd) settings
version_added: "0.0.1"
description:
    - Configure Remote Syslog settings in a UniFi controller.
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
    enabled:
        description: Whether remote syslog is enabled.
        type: bool
        default: true
    ip:
        description: IP address of the syslog server.
        type: str
        required: false
    port:
        description: Port of the syslog server.
        type: int
        default: 10516
    log_all_contents:
        description: Whether to log all contents.
        type: bool
        default: true
    debug:
        description: Whether to enable debug logging.
        type: bool
        default: false
    netconsole_enabled:
        description: Whether to enable netconsole.
        type: bool
        default: false
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
        enabled=dict(type="bool", default=True),
        ip=dict(type="str", required=False),
        port=dict(type="int", default=10516),
        log_all_contents=dict(type="bool", default=True),
        debug=dict(type="bool", default=False),
        netconsole_enabled=dict(type="bool", default=False),
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

    # Fetch current settings
    res, info = api.request(f"/proxy/network/api/s/{site}/get/setting")
    settings = api.as_list(res)

    current = next((s for s in settings if isinstance(s, dict) and s.get("key") == "rsyslogd"), None)

    if not current:
        module.fail_json(msg="rsyslogd setting not found on controller")

    desired_payload = {
        "key": "rsyslogd",
        "enabled": module.params["enabled"],
        "ip": module.params["ip"],
        "port": module.params["port"],
        "log_all_contents": module.params["log_all_contents"],
        "debug": module.params["debug"],
        "netconsole_enabled": module.params["netconsole_enabled"],
        "this_controller": False,
        "this_controller_encrypted_only": False
    }

    changed = False
    for key, value in desired_payload.items():
        if current.get(key) != value:
            changed = True
            break

    if changed:
        if not module.check_mode:
            res, info = api.request(
                f"/proxy/network/api/s/{site}/set/setting/rsyslogd/{current['_id']}",
                method="PUT",
                data=desired_payload
            )
            if not res:
                module.fail_json(msg="Failed to update rsyslogd settings", info=info)
            current = api.as_list(res)[0] if api.as_list(res) else res

    module.exit_json(changed=changed, setting=current)


if __name__ == "__main__":
    run_module()
