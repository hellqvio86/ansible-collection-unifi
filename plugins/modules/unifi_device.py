#!/usr/bin/python
# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: unifi_device
short_description: Manage UniFi devices (Access Points, Switches, Gateways)
version_added: "0.0.32"
description:
    - Adopt, configure, or remove (forget) UniFi hardware devices on a UniFi controller.
    - Supports setting device names, aliases, LED status, management VLAN/network,
      outdoor mode, notes, and disabling devices.
    - Can trigger device adoption for pending devices and toggle locate LED flashing.
    - Uses the UniFi controller device endpoints C(/proxy/network/api/s/{site}/stat/device) and C(/rest/device).
options:
    host:
        description: The host or IP address of the UniFi controller.
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
    unifi_session_cookie:
        description: Pre-authenticated session cookie string.
        type: str
        required: false
    unifi_csrf_token:
        description: Pre-authenticated CSRF token.
        type: str
        required: false
    state:
        description:
            - Whether the device should be managed (C(present)) or removed/forgotten (C(absent)).
        choices: [ present, absent ]
        default: present
        type: str
    mac:
        description:
            - MAC address of the device to manage (e.g. C(aa:bb:cc:dd:ee:ff)).
            - Case-insensitive and accepts dash, dot, or colon delimiters.
            - At least one of C(mac), C(name), or C(id) must be specified.
        required: false
        type: str
    name:
        description:
            - User-defined name or alias for the device.
            - Can be used to find an existing device if C(mac) is not specified, or
              to update the device name when C(mac) is provided.
        required: false
        type: str
    id:
        description:
            - Unique identifier (C(_id)) of the device for explicit ID-based targeting or renaming.
        required: false
        type: str
    adopt:
        description:
            - Automatically adopt the device if it is in a pending-adoption state.
        type: bool
        default: true
    disabled:
        description:
            - Whether the device is disabled in the controller.
        type: bool
        required: false
    led_override:
        description:
            - Device LED ring or indicator override setting.
        choices: [ default, "on", "off" ]
        type: str
        required: false
    led_override_color:
        description:
            - Custom LED color in hex format (e.g. C(#0000ff)) for supported hardware.
        type: str
        required: false
    led_override_color_brightness:
        description:
            - Custom LED brightness percentage (1-100) for supported hardware.
        type: int
        required: false
    outdoor_mode_override:
        description:
            - Outdoor mode override for Access Points.
        choices: [ default, "on", "off" ]
        type: str
        required: false
    mgmt_network:
        description:
            - Name or ID of the network / VLAN to use for management traffic.
        type: str
        required: false
    note:
        description:
            - User note or comment stored on the device.
        type: str
        required: false
    locate:
        description:
            - Trigger flashing locate LED on the device.
            - C(true) turns on locate blinking, C(false) turns it off.
        type: bool
        required: false
author:
    - Olof Hellqvist (@hellqvio86)
"""

EXAMPLES = r"""
- name: Adopt and name a new Access Point
  hellqvio86.unifi.unifi_device:
    mac: "70:a7:41:11:22:33"
    name: "AP-LivingRoom"
    state: present
    adopt: true
    led_override: "off"

- name: Set management network and note on a switch
  hellqvio86.unifi.unifi_device:
    name: "USW-Core"
    mgmt_network: "Management VLAN"
    note: "Rack 1 Switch"
    state: present

- name: Forget/remove a device from controller
  hellqvio86.unifi.unifi_device:
    mac: "70:a7:41:11:22:33"
    state: absent
"""

RETURN = r"""
changed:
    description: Whether the device was adopted, updated, or removed.
    type: bool
    returned: always
device:
    description: Sanitized device information from the controller.
    type: dict
    returned: when device exists
    sample:
        _id: "60f1b2c3d4e5f6a7b8c9d0e1"
        name: "AP-LivingRoom"
        mac: "70:a7:41:11:22:33"
        model: "U6-Pro"
        type: "uap"
        ip: "192.168.1.55"
        version: "6.5.54"
        adopted: true
        state: 1
        disabled: false
        led_override: "off"
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import (
    UnifiAPI,
    make_diff,
    validate_mac_address,
)

_DEVICE_SAFE_FIELDS = (
    "_id",
    "name",
    "mac",
    "model",
    "type",
    "ip",
    "version",
    "adopted",
    "state",
    "disabled",
    "led_override",
    "led_override_color",
    "led_override_color_brightness",
    "outdoor_mode_override",
    "mgmt_network_id",
    "note",
    "uptime",
    "last_seen",
    "site_id",
    "serial",
)


def _sanitize_device(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract and sanitize device properties for return values."""
    res: dict[str, Any] = {}
    for key in _DEVICE_SAFE_FIELDS:
        if key in raw:
            res[key] = raw[key]
    return res


def _find_matching_device(
    module: AnsibleModule,
    devices: list[Any],
    mac: str | None,
    name: str | None,
    device_id: str | None,
) -> dict[str, Any] | None:
    """Find a single device matching id, mac, or name."""
    if device_id:
        matches = [
            d for d in devices if isinstance(d, dict) and (d.get("_id") == device_id or d.get("id") == device_id)
        ]
        if len(matches) > 1:
            module.fail_json(msg=f"Ambiguous device: multiple devices match id '{device_id}'")
        return matches[0] if matches else None

    if mac:
        matches = [d for d in devices if isinstance(d, dict) and d.get("mac", "").lower() == mac.lower()]
        if len(matches) > 1:
            module.fail_json(msg=f"Ambiguous device: multiple devices match MAC '{mac}'")
        return matches[0] if matches else None

    if name:
        matches = [
            d
            for d in devices
            if isinstance(d, dict)
            and (d.get("name") == name or (not d.get("name") and d.get("mac", "").lower() == name.lower()))
        ]
        if len(matches) > 1:
            module.fail_json(msg=f"Ambiguous device: multiple devices match name '{name}'")
        return matches[0] if matches else None

    return None


def run_module() -> None:
    """Execute unifi_device module logic."""
    module_args: dict[str, Any] = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        mac=dict(type="str", required=False),
        name=dict(type="str", required=False),
        id=dict(type="str", required=False),
        adopt=dict(type="bool", default=True),
        disabled=dict(type="bool", required=False),
        led_override=dict(type="str", choices=["default", "on", "off"], required=False),
        led_override_color=dict(type="str", required=False),
        led_override_color_brightness=dict(type="int", required=False),
        outdoor_mode_override=dict(type="str", choices=["default", "on", "off"], required=False),
        mgmt_network=dict(type="str", required=False),
        note=dict(type="str", required=False),
        locate=dict(type="bool", required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    state: str = module.params["state"]
    mac_param: str | None = module.params.get("mac")
    name_param: str | None = module.params.get("name")
    id_param: str | None = module.params.get("id")

    if not mac_param and not name_param and not id_param:
        module.fail_json(msg="At least one of 'mac', 'name', or 'id' must be specified to identify the device")

    norm_mac: str | None = None
    if mac_param:
        norm_mac = validate_mac_address(module, mac_param, "mac")

    brightness = module.params.get("led_override_color_brightness")
    if brightness is not None and not (1 <= brightness <= 100):
        module.fail_json(msg=f"'led_override_color_brightness' must be between 1 and 100, got {brightness}")

    api = UnifiAPI(
        module,
        module.params.get("host"),
        module.params.get("username"),
        module.params.get("password"),
        module.params.get("validate_certs"),
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    site = module.params["site"]

    # Fetch devices from stat/device or rest/device
    res, info = api.request(f"/proxy/network/api/s/{site}/stat/device")
    if res is None and info.get("status") == 404:
        res, info = api.request(f"/proxy/network/api/s/{site}/rest/device")
    if info.get("status") != 200:
        module.fail_json(msg="Failed to fetch devices from controller", info=info)

    devices = api.as_list(res)
    existing = _find_matching_device(module, devices, norm_mac, name_param, id_param)

    # Handle absent
    if state == "absent":
        if existing is None:
            module.exit_json(changed=False, msg="Device is not registered on controller")
            return

        dev_id = existing.get("_id")
        dev_mac = existing.get("mac")
        diff = make_diff(existing, {})

        if module.check_mode:
            module.exit_json(changed=True, diff=diff)
            return

        # Try DELETE /rest/device/{id}
        del_res, del_info = api.request(f"/proxy/network/api/s/{site}/rest/device/{dev_id}", method="DELETE")
        if del_info.get("status") not in (200, 204):
            # Fallback to cmd/sitemgr delete-device
            cmd_res, cmd_info = api.request(
                f"/proxy/network/api/s/{site}/cmd/sitemgr",
                method="POST",
                data={"cmd": "delete-device", "mac": dev_mac},
            )
            if cmd_info.get("status") not in (200, 201):
                module.fail_json(msg="Failed to remove/forget device", info=del_info, fallback_info=cmd_info)

        module.exit_json(changed=True, diff=diff)
        return

    # Handle present
    if existing is None:
        ident = norm_mac or name_param or id_param
        module.fail_json(
            msg=(
                f"Device '{ident}' not found on controller. UniFi devices must be connected or "
                "discovered before they can be configured."
            )
        )

    dev_id = existing.get("_id")
    dev_mac = existing.get("mac")
    changed = False
    before_diff: dict[str, Any] = {}
    after_diff: dict[str, Any] = {}

    # Check adoption
    adopt_requested: bool = module.params.get("adopt", True)
    is_adopted: bool = bool(existing.get("adopted", True))
    # In UniFi, state 2 typically indicates pending adoption
    is_pending: bool = not is_adopted or existing.get("state") == 2

    if adopt_requested and is_pending:
        before_diff["adopted"] = False
        after_diff["adopted"] = True
        changed = True
        if not module.check_mode:
            adopt_res, adopt_info = api.request(
                f"/proxy/network/api/s/{site}/cmd/devmgr",
                method="POST",
                data={"cmd": "adopt", "mac": dev_mac},
            )
            if adopt_info.get("status") not in (200, 201):
                module.fail_json(msg="Failed to adopt device", info=adopt_info)

    # Resolve management network if requested
    mgmt_net_param = module.params.get("mgmt_network")
    desired_mgmt_id: str | None = None
    if mgmt_net_param:
        net_res, net_info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
        if net_info.get("status") == 200:
            nets = api.as_list(net_res)
            match_net = next(
                (
                    n
                    for n in nets
                    if isinstance(n, dict) and (n.get("name") == mgmt_net_param or n.get("_id") == mgmt_net_param)
                ),
                None,
            )
            if match_net:
                desired_mgmt_id = match_net.get("_id")
            else:
                desired_mgmt_id = mgmt_net_param
        else:
            desired_mgmt_id = mgmt_net_param

    # Check locate command
    locate_param = module.params.get("locate")
    if locate_param is not None:
        current_locating = bool(existing.get("locating", False))
        if locate_param != current_locating:
            before_diff["locating"] = current_locating
            after_diff["locating"] = locate_param
            changed = True
            if not module.check_mode:
                loc_cmd = "set-locate" if locate_param else "unset-locate"
                api.request(
                    f"/proxy/network/api/s/{site}/cmd/devmgr",
                    method="POST",
                    data={"cmd": loc_cmd, "mac": dev_mac},
                )

    # Build desired payload for device configuration
    desired_update: dict[str, Any] = {}

    if name_param is not None:
        cur_name = existing.get("name") or ""
        if cur_name != name_param:
            desired_update["name"] = name_param
            before_diff["name"] = cur_name
            after_diff["name"] = name_param

    disabled_param = module.params.get("disabled")
    if disabled_param is not None:
        cur_disabled = bool(existing.get("disabled", False))
        if cur_disabled != disabled_param:
            desired_update["disabled"] = disabled_param
            before_diff["disabled"] = cur_disabled
            after_diff["disabled"] = disabled_param

    led_param = module.params.get("led_override")
    if led_param is not None:
        cur_led = existing.get("led_override", "default")
        if cur_led != led_param:
            desired_update["led_override"] = led_param
            before_diff["led_override"] = cur_led
            after_diff["led_override"] = led_param

    color_param = module.params.get("led_override_color")
    if color_param is not None:
        cur_color = existing.get("led_override_color", "")
        if cur_color != color_param:
            desired_update["led_override_color"] = color_param
            before_diff["led_override_color"] = cur_color
            after_diff["led_override_color"] = color_param

    bright_param = module.params.get("led_override_color_brightness")
    if bright_param is not None:
        cur_bright = existing.get("led_override_color_brightness")
        if cur_bright != bright_param:
            desired_update["led_override_color_brightness"] = bright_param
            before_diff["led_override_color_brightness"] = cur_bright
            after_diff["led_override_color_brightness"] = bright_param

    outdoor_param = module.params.get("outdoor_mode_override")
    if outdoor_param is not None:
        cur_outdoor = existing.get("outdoor_mode_override", "default")
        if cur_outdoor != outdoor_param:
            desired_update["outdoor_mode_override"] = outdoor_param
            before_diff["outdoor_mode_override"] = cur_outdoor
            after_diff["outdoor_mode_override"] = outdoor_param

    if desired_mgmt_id is not None:
        cur_mgmt = existing.get("mgmt_network_id")
        if cur_mgmt != desired_mgmt_id:
            desired_update["mgmt_network_id"] = desired_mgmt_id
            before_diff["mgmt_network_id"] = cur_mgmt
            after_diff["mgmt_network_id"] = desired_mgmt_id

    note_param = module.params.get("note")
    if note_param is not None:
        cur_note = existing.get("note", "")
        if cur_note != note_param:
            desired_update["note"] = note_param
            before_diff["note"] = cur_note
            after_diff["note"] = note_param

    if desired_update:
        changed = True
        if not module.check_mode:
            upd_res, upd_info = api.request(
                f"/proxy/network/api/s/{site}/rest/device/{dev_id}",
                method="PUT",
                data=desired_update,
            )
            if upd_info.get("status") != 200:
                module.fail_json(msg="Failed to update device configuration", info=upd_info)
            if isinstance(upd_res, dict) and "data" in upd_res and upd_res["data"]:
                existing = upd_res["data"][0]
            elif isinstance(upd_res, list) and upd_res:
                existing = upd_res[0]
            else:
                existing.update(desired_update)

    diff_result = make_diff(before_diff, after_diff) if changed else {}
    sanitized = _sanitize_device(existing)
    module.exit_json(changed=changed, diff=diff_result, device=sanitized)


def main() -> None:
    """Entry point for unifi_device."""
    run_module()


if __name__ == "__main__":
    main()
