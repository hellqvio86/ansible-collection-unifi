# hellqvio86.unifi.unifi_firewall_zone

Manage UniFi v8.3+ Firewall Zones (Policy Engine)

## Description
Create, update, or delete firewall zones in a UniFi controller using the modern Policy Engine.

This module targets the v2 API introduced in UniFi Network 8.x.

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
| `id` | str | No |  | ID of the firewall zone. |
| `state` | str | No | `present` | Whether the firewall zone should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the firewall zone. |
| `type` | str | No | `custom` | Type of the firewall zone. Choices: `lan`, `wan`, `guest`, `iot`, `custom`. |
| `description` | str | No |  | Description of the firewall zone. |

## Examples

```yaml
- name: Create LAN firewall zone
  hellqvio86.unifi.unifi_firewall_zone:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    site: "default"
    validate_certs: true
    name: "Internal"
    type: lan
    description: "Main LAN zone"
    state: present
```
