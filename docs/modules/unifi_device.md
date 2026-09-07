# hellqvio86.unifi.unifi_device

Manage UniFi devices (Access Points, Switches, Gateways)

## Description
Adopt, configure, or remove (forget) UniFi hardware devices on a UniFi controller.

Supports setting device names, aliases, LED status, management VLAN/network, outdoor mode, notes, and disabling devices.

Can trigger device adoption for pending devices and toggle locate LED flashing.

Uses the UniFi controller device endpoints `/proxy/network/api/s/{site}/stat/device` and `/rest/device`.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host or IP address of the UniFi controller. |
| `username` | str | No |  | UniFi controller username. |
| `password` | str | No |  | UniFi controller password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `state` | str | No | `present` | Whether the device should be managed (`present`) or removed/forgotten (`absent`). Choices: `present`, `absent`. |
| `mac` | str | No |  | MAC address of the device to manage (e.g. `aa:bb:cc:dd:ee:ff`). Case-insensitive and accepts dash, dot, or colon delimiters. At least one of `mac`, `name`, or `id` must be specified. |
| `name` | str | No |  | User-defined name or alias for the device. Can be used to find an existing device if `mac` is not specified, or to update the device name when `mac` is provided. |
| `id` | str | No |  | Unique identifier (`_id`) of the device for explicit ID-based targeting or renaming. |
| `adopt` | bool | No | `True` | Automatically adopt the device if it is in a pending-adoption state. |
| `disabled` | bool | No |  | Whether the device is disabled in the controller. |
| `led_override` | str | No |  | Device LED ring or indicator override setting. Choices: `default`, `on`, `off`. |
| `led_override_color` | str | No |  | Custom LED color in hex format (e.g. `#0000ff`) for supported hardware. |
| `led_override_color_brightness` | int | No |  | Custom LED brightness percentage (1-100) for supported hardware. |
| `outdoor_mode_override` | str | No |  | Outdoor mode override for Access Points. Choices: `default`, `on`, `off`. |
| `mgmt_network` | str | No |  | Name or ID of the network / VLAN to use for management traffic. |
| `note` | str | No |  | User note or comment stored on the device. |
| `locate` | bool | No |  | Trigger flashing locate LED on the device. `true` turns on locate blinking, `false` turns it off. |

## Examples

```yaml
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
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether the device was adopted, updated, or removed. |
| `device` | dict | when device exists | Sanitized device information from the controller. |
