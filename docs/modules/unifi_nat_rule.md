# hellqvio86.unifi.unifi_nat_rule

Manage UniFi Source NAT / Masquerade rules via the controller API

## Description
Creates, updates, or deletes Source NAT (SNAT) or Masquerade rules on a UniFi controller using the `/proxy/network/v2/api/site/{site}/firewall/nat` endpoint.

Rules are matched by name for idempotency; an existing rule with the same name is updated in-place rather than duplicated.

This module never uses SSH or direct iptables; all changes go through the HTTP API.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | Hostname or IP address of the UniFi controller. |
| `username` | str | No |  | Controller admin username. |
| `password` | str | No |  | Controller admin password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Validate TLS certificates on the controller. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `api_key` | str | No |  | Token for direct API authentication. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie (skips login step). |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token (skips login step). |
| `id` | str | No |  | ID of the NAT rule. |
| `state` | str | No | `present` | Whether the rule should exist. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Human-readable name for the rule. Used as the idempotency key — the module matches rules by this name. |
| `type` | str | No | `masquerade` | NAT rule type. `masquerade` hides the source behind the outbound interface IP (many-to-one). `snat` translates the source address. `dnat` translates the destination address. Choices: `masquerade`, `snat`, `dnat`. |
| `src_address` | str | No | `` | Source IP or CIDR to match before translation (e.g. `192.0.2.10` or `192.0.2.0/24`). |
| `dst_address` | str | No | `` | Destination IP or CIDR to match (e.g. `198.51.100.0/24`). Leave empty to match any destination. |
| `outbound_interface` | str | No | `` | UniFi network name whose interface is used as the post-NAT egress interface. The module resolves the human-readable name to the internal `_id` via `/proxy/network/api/s/{site}/rest/networkconf`. Required for `masquerade`; optional for `source`. |
| `translated_src` | str | No | `` | For `type=source` — the specific IP to translate the source address to. Not used for `masquerade`. |
| `enabled` | bool | No | `True` | Whether the rule is active. |
| `logging` | bool | No | `False` | Whether to log packets matching this rule. |

## Examples

```yaml
- name: Masquerade Home Assistant traffic to Generic IoT subnet
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Generic IoT"
    type: masquerade
    src_address: "192.0.2.10"
    dst_address: "198.51.100.0/24"
    outbound_interface: "LAN_IoT"
    enabled: true

- name: Source-NAT to a specific translated address
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT gateway traffic"
    type: source
    src_address: "198.51.100.0/24"
    dst_address: ""
    translated_src: "203.0.113.5"
    enabled: true

- name: Remove a NAT rule
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Generic IoT"
    src_address: "192.0.2.10"
    state: absent
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether a change was applied to the controller. |
| `rule` | dict | always | Current state of the NAT rule after the operation, or null if deleted. |
