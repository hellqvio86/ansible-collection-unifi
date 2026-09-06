# hellqvio86.unifi.unifi_firewall_policy

Manage UniFi v8.3+ Policy Engine Firewall Rules

## Description
Create, update, or delete firewall policies in a UniFi controller using the modern Policy Engine (Zone-Based Firewall).

This module targets the v2 API introduced in UniFi Network 8.x.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller (e.g., 192.0.2.1). |
| `username` | str | No |  | UniFi controller username. |
| `password` | str | No |  | UniFi controller password. |
| `site` | str | No | `default` | UniFi site name (typically 'default'). |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `id` | str | No |  | ID of the firewall policy. |
| `state` | str | No | `present` | Whether the policy should be present or absent. Choices: `present`, `absent`. |
| `name` | str | No |  | Name of the firewall policy. |
| `action` | str | No | `ALLOW` | Action to take. Choices: `ALLOW`, `BLOCK`, `REJECT`, `ISOLATE`. |
| `protocol` | str | No | `all` | Protocol to match. Choices: `all`, `tcp`, `udp`, `tcp_udp`, `icmp`, `icmpv6`. |
| `ip_version` | str | No |  | IP version to apply policy to. Choices: `BOTH`, `IPV4`, `IPV6`. |
| `connection_state_type` | str | No | `ALL` | Connection state type. Choices: `ALL`, `RESPOND_ONLY`, `CUSTOM`. |
| `connection_states` | list | No | `[]` | List of connection states when connection_state_type is CUSTOM. Choices: `NEW`, `ESTABLISHED`, `RELATED`, `INVALID`. |
| `create_allow_respond` | bool | No |  | Automatically create a return rule to allow response traffic. |
| `index` | int | No | `10000` | Rule index (order). |
| `enabled` | bool | No | `True` | Whether the rule is enabled. |
| `logging` | bool | No | `False` | Whether to log matches. |
| `source` | dict | No |  | Source configuration. |
| `destination` | dict | No |  | Destination configuration. |
| `policies` | list | No |  | List of firewall policies to create, update, or remove in batch. |

## Examples

```yaml
- name: Block IoT to Gateway
  hellqvio86.unifi.unifi_firewall_policy:
    name: "Block IoT to Gateway"
    action: BLOCK
    source:
      zone: "Internal"
      ips: ["203.0.113.0/24"]
    destination:
      zone: "External"
    protocol: all
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `firewall_policy` | dict | always | Details of the firewall policy. |
