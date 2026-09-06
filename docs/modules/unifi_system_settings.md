# hellqvio86.unifi.unifi_system_settings

Manage UniFi system-wide settings (NTP, timezone, management)

## Description
Configure system-wide NTP servers, timezone, management (LED, SSH), and device settings on a UniFi controller.

Uses the `/proxy/network/api/s/{site}/set/setting/ntp` and `/proxy/network/api/s/{site}/set/setting/mgmt` endpoints.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller. |
| `username` | str | No |  | UniFi controller username. |
| `password` | str | No |  | UniFi controller password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `ntp` | dict | No |  | NTP server and timezone configuration. Maps to the `setting/ntp` endpoint. |
| `mgmt` | dict | No |  | Management settings (LED, SSH). Maps to the `setting/mgmt` endpoint. |
| `switch` | dict | No |  | Global switch settings (DHCP snooping, flow control, jumbo frames, STP). Maps to the `setting/global_switch` endpoint. |

## Examples

```yaml
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
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether any change was applied. |
| `settings` | dict | always | Current state of the ntp and mgmt settings after the operation. |
