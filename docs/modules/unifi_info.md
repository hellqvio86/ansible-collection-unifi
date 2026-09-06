# hellqvio86.unifi.unifi_info

Gather information about UniFi infrastructure

## Description
Gather details about WiFi networks, firewall groups, zones, policies, and settings from a UniFi controller.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller (IP or FQDN). |
| `username` | str | No |  | UniFi controller administrator username. |
| `password` | str | No |  | UniFi controller administrator password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `api_key` | str | No |  | Token for direct API authentication. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `gather_subset` | list | No | `['wifi', 'firewall_groups', 'firewall_zones', 'firewall_policies', 'rsyslog']` | List of subsets to gather. Choices: `wifi`, `firewall_groups`, `firewall_zones`, `firewall_policies`, `rsyslog`, `port_profiles`, `devices`, `dhcp_reservations`, `networks`, `system_settings`, `port_forward`. |

## Examples

```yaml
- name: Gather all UniFi state
  hellqvio86.unifi.unifi_info:
    gather_subset:
      - wifi
      - firewall_groups
      - firewall_zones
      - firewall_policies
      - rsyslog
      - port_profiles
  register: unifi_state

- name: Gather WiFi details
  hellqvio86.unifi.unifi_info:
    gather_subset: ["wifi"]
  register: wifi_state
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `unifi_info` | dict | always | Information gathered from the UniFi controller keyed by subset. |
