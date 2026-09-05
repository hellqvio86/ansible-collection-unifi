#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

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

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
    UnifiAPI,
    make_diff,
    resource_has_drift,
    validate_ip_address,
    validate_port,
)


def _build_desired_payload(params: dict) -> dict:
    """Build the desired rsyslogd setting payload from module parameters."""
    return {
        "key": "rsyslogd",
        "enabled": params["enabled"],
        "ip": params.get("ip"),
        "port": params["port"],
        "log_all_contents": params["log_all_contents"],
        "debug": params["debug"],
        "netconsole_enabled": params["netconsole_enabled"],
        "this_controller": False,
        "this_controller_encrypted_only": False,
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
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    # Validate argument formats before making any API calls
    if module.params.get("ip"):
        validate_ip_address(module, module.params["ip"], "ip")
    validate_port(module, module.params["port"], "port")

    site = module.params["site"]

    # Fetch current settings
    res, info = api.request(f"/proxy/network/api/s/{site}/get/setting")
    settings = api.as_list(res)
    matches = [s for s in settings if isinstance(s, dict) and s.get("key") == "rsyslogd"]
    if len(matches) > 1:
        module.fail_json(msg="Ambiguous resource: multiple rsyslogd settings found on controller")
    current = matches[0] if matches else None

    if not current:
        module.fail_json(msg="rsyslogd setting not found on controller")

    desired_payload = _build_desired_payload(module.params)

    changed = resource_has_drift(current, desired_payload)

    result_setting = current
    if changed:
        if not module.check_mode:
            res, info = api.request(
                f"/proxy/network/api/s/{site}/set/setting/rsyslogd/{current['_id']}", method="PUT", data=desired_payload
            )
            if not res:
                module.fail_json(msg="Failed to update rsyslogd settings", info=info)
            result_setting = api.as_list(res)[0] if api.as_list(res) else res
        else:
            result_setting = {**current, **desired_payload}

    exit_kwargs = {"changed": changed, "setting": result_setting}
    if getattr(module, "_diff", False) is True:
        before = current if current else {}
        after = result_setting if result_setting else {}
        exit_kwargs["diff"] = make_diff(before, after)


    module.exit_json(**exit_kwargs)



if __name__ == "__main__":
    run_module()
