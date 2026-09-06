# hellqvio86.unifi.unifi_firewall_group

Manage UniFi firewall groups (address or port groups)

## Description
Create, update, or delete firewall groups in a UniFi controller.

Supports both address-group (IPs/Networks) and port-group (Ports).

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
| `id` | str | No |  | ID of the firewall group. |
| `state` | str | No | `present` | Whether the group should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the firewall group. |
| `group_type` | str | No | `address-group` | Type of the group. Choices: `address-group`, `port-group`. |
| `group_members` | list | No |  | List of members (IPs, networks, or ports). |

## Examples

```yaml
- name: Ensure web ports group exists
  hellqvio86.unifi.unifi_firewall_group:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Web Ports"
    group_type: "port-group"
    group_members: ["80", "443"]

- name: Ensure internal networks group exists
  hellqvio86.unifi.unifi_firewall_group:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Internal Networks"
    group_type: "address-group"
    group_members: ["192.0.2.0/24", "198.51.100.0/24"]
```
