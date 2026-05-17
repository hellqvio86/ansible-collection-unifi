#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_system_settings
short_description: Manage UniFi system-wide settings (NTP, timezone, management)
version_added: "0.0.7"
description:
    - Configure system-wide NTP servers, timezone, management (LED, SSH), and device settings on a UniFi controller.
    - Uses the C(/proxy/network/api/s/{site}/set/setting/ntp) and C(/proxy/network/api/s/{site}/set/setting/mgmt) endpoints.
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
    ntp:
        description:
            - NTP server and timezone configuration.
            - Maps to the C(setting/ntp) endpoint.
        type: dict
        suboptions:
            server_1:
                description: Primary NTP server.
                type: str
            server_2:
                description: Secondary NTP server.
                type: str
            server_3:
                description: Tertiary NTP server.
                type: str
            server_4:
                description: Quaternary NTP server.
                type: str
            timezone:
                description:
                    - Timezone string (e.g., C(Europe/Stockholm)).
                type: str
    mgmt:
        description:
            - Management settings (LED, SSH).
            - Maps to the C(setting/mgmt) endpoint.
        type: dict
        suboptions:
            led_enabled:
                description:
                    - Whether device LEDs are enabled globally.
                type: bool
            ssh_password_enabled:
                description:
                    - Whether SSH password authentication is enabled.
                    - Maps to C(x_ssh_auth_password_enabled).
                type: bool
            ssh_bind_wildcard:
                description:
                    - Whether SSH binds to all interfaces (0.0.0.0).
                    - Maps to C(x_ssh_bind_wildcard).
                type: bool
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Configure NTP servers and timezone
  hellqvio86.unifi.unifi_system_settings:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    ntp:
      server_1: "0.pool.ntp.org"
      server_2: "1.pool.ntp.org"
      timezone: "Europe/Stockholm"

- name: Disable device LEDs
  hellqvio86.unifi.unifi_system_settings:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mgmt:
      led_enabled: false

- name: Disable SSH password auth
  hellqvio86.unifi.unifi_system_settings:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mgmt:
      ssh_password_enabled: false

- name: Configure both NTP and management settings
  hellqvio86.unifi.unifi_system_settings:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    ntp:
      server_1: "0.pool.ntp.org"
      server_2: "1.pool.ntp.org"
      server_3: ""
      server_4: ""
      timezone: "Europe/Stockholm"
    mgmt:
      led_enabled: true
      ssh_password_enabled: false
"""

RETURN = r"""
changed:
    description: Whether any change was applied.
    type: bool
    returned: always
settings:
    description: Current state of the ntp and mgmt settings after the operation.
    type: dict
    returned: always
    sample: {"ntp": {"ntp_server_1": "0.pool.ntp.org", "timezone": "Europe/Stockholm"}, "mgmt": {"led_enabled": true, "x_ssh_auth_password_enabled": false}}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI

NTP_FIELD_MAP = {
    "server_1": "ntp_server_1",
    "server_2": "ntp_server_2",
    "server_3": "ntp_server_3",
    "server_4": "ntp_server_4",
    "timezone": "timezone",
}

MGMT_FIELD_MAP = {
    "led_enabled": "led_enabled",
    "ssh_password_enabled": "x_ssh_auth_password_enabled",
    "ssh_bind_wildcard": "x_ssh_bind_wildcard",
}


def _build_ntp_payload(ntp_params):
    payload = {"key": "ntp"}
    for param_key, api_key in NTP_FIELD_MAP.items():
        if ntp_params.get(param_key) is not None:
            payload[api_key] = ntp_params[param_key]
    return payload


def _build_mgmt_payload(mgmt_params):
    payload = {"key": "mgmt"}
    for param_key, api_key in MGMT_FIELD_MAP.items():
        if mgmt_params.get(param_key) is not None:
            payload[api_key] = mgmt_params[param_key]
    return payload


def _check_changed(current, desired):
    for key, value in desired.items():
        if current.get(key) != value:
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
        ntp=dict(
            type="dict",
            options=dict(
                server_1=dict(type="str"),
                server_2=dict(type="str"),
                server_3=dict(type="str"),
                server_4=dict(type="str"),
                timezone=dict(type="str"),
            ),
        ),
        mgmt=dict(
            type="dict",
            options=dict(
                led_enabled=dict(type="bool"),
                ssh_password_enabled=dict(type="bool"),
                ssh_bind_wildcard=dict(type="bool"),
            ),
        ),
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

    res, info = api.request(f"/proxy/network/api/s/{site}/get/setting")
    if info["status"] != 200:
        module.fail_json(msg="Failed to fetch system settings", info=info)

    settings = api.as_list(res)

    changed = False
    result_settings = {}

    ntp_params = module.params.get("ntp")
    mgmt_params = module.params.get("mgmt")

    # Handle NTP settings
    if ntp_params is not None:
        current_ntp = next(
            (s for s in settings if isinstance(s, dict) and s.get("key") == "ntp"),
            None,
        )
        if not current_ntp:
            module.fail_json(msg="NTP setting not found on controller")

        desired_ntp = _build_ntp_payload(ntp_params)

        if _check_changed(current_ntp, desired_ntp):
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/set/setting/ntp/{current_ntp['_id']}",
                    method="PUT",
                    data=desired_ntp,
                )
                if not res:
                    module.fail_json(msg="Failed to update NTP settings", info=info)
                current_ntp = api.as_list(res)[0] if api.as_list(res) else res

        result_settings["ntp"] = current_ntp

    # Handle management (mgmt) settings
    if mgmt_params is not None:
        current_mgmt = next(
            (s for s in settings if isinstance(s, dict) and s.get("key") == "mgmt"),
            None,
        )
        if not current_mgmt:
            module.fail_json(msg="Management setting not found on controller")

        desired_mgmt = _build_mgmt_payload(mgmt_params)

        if _check_changed(current_mgmt, desired_mgmt):
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/set/setting/mgmt/{current_mgmt['_id']}",
                    method="PUT",
                    data=desired_mgmt,
                )
                if not res:
                    module.fail_json(msg="Failed to update management settings", info=info)
                current_mgmt = api.as_list(res)[0] if api.as_list(res) else res

        result_settings["mgmt"] = current_mgmt

    module.exit_json(changed=changed, settings=result_settings)


if __name__ == "__main__":
    run_module()
