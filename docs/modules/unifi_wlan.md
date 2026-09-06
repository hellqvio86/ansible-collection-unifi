# hellqvio86.unifi.unifi_wlan

Manage UniFi wireless network (WLAN) configurations

## Description
Create, update, or delete UniFi WLAN configurations.

This module manages the controller's wireless network definitions in the configured site.

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
| `id` | str | No |  | ID of the WLAN configuration. |
| `state` | str | No | `present` | Whether the WLAN should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the wireless network (SSID). |
| `enabled` | bool | No |  | Enable or disable the WLAN. |
| `network_name` | str | No |  | Name of the associated network profile. |
| `security` | str | No |  | Security mode for the WLAN. Choices: `open`, `wpapsk`, `wpa2`, `wpa3`. |
| `passphrase` | str | No |  | WPA passphrase for secured networks. |
| `band` | str | No |  | Band restriction for the WLAN. Use 'both' for dual-band, '2g' for 2.4 GHz only, '5g' for 5 GHz only. Choices: `both`, `2g`, `5g`. |

## Examples

```yaml
- name: Ensure guest SSID exists
  hellqvio86.unifi.unifi_wlan:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: true
    name: "Guest WLAN"
    enabled: true
    network_name: "Guest"
    security: wpapsk
    passphrase: "supersecret"
    state: present
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `wlan` | dict | when state is present | The created or updated WLAN configuration object. |
