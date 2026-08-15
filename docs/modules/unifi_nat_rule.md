# hellqvio86.unifi.unifi_nat_rule

Manage UniFi Source NAT / Masquerade rules via the controller API.

## Description

This module creates, updates, or deletes Source NAT (SNAT) or Masquerade rules on a UniFi
controller using the `/proxy/network/v2/api/site/{site}/firewall/nat` endpoint.

Rules are matched by **name** for idempotency — an existing rule with the same name is
updated in-place rather than duplicated. All changes go through the HTTP API; SSH and
direct iptables access are never used.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Idempotency key; shown in the controller UI. |
| `state` | str | No | `present` | `present` or `absent`. |
| `type` | str | No | `masquerade` | `masquerade` (hide behind interface IP) or `source` (translate to specific IP). |
| `src_address` | str | Yes | | Source IP or CIDR to match before translation. |
| `dst_address` | str | No | `""` | Destination IP or CIDR to match. Empty = any. |
| `outbound_interface` | str | No | `""` | UniFi network name to use as the post-NAT egress interface. Resolved to internal ID via `networkconf`. |
| `translated_src` | str | No | `""` | For `type=source` — the IP to translate the source to. |
| `enabled` | bool | No | `true` | Whether the rule is active. |
| `logging` | bool | No | `false` | Whether to log matching packets. |
| `host` | str | No | | Controller hostname or IP (or `UNIFI_HOST` env var). |
| `username` | str | No | | Admin username (or `UNIFI_USERNAME` env var). |
| `password` | str | No | | Admin password (or `UNIFI_PASSWORD` env var). |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `false` | Validate controller TLS certificate. |
| `unifi_session_cookie` | str | No | | Pre-authenticated session cookie. |
| `unifi_csrf_token` | str | No | | Pre-authenticated CSRF token. |

## Examples

### Masquerade Home Assistant traffic to an IoT subnet

```yaml
- name: SNAT Home Assistant to Xiaomi IoT
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Xiaomi IoT"
    type: masquerade
    src_address: "192.0.2.10"
    dst_address: "198.51.100.0/24"
    outbound_interface: "LAN_IoT"
    enabled: true
```

### Source NAT to a specific translated address

```yaml
- name: SNAT gateway traffic to fixed WAN IP
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT gateway traffic"
    type: source
    src_address: "198.51.100.0/24"
    translated_src: "203.0.113.5"
    enabled: true
```

### Remove a NAT rule

```yaml
- name: Remove SNAT rule
  hellqvio86.unifi.unifi_nat_rule:
    host: "192.0.2.1"
    username: "admin"
    password: "secret"
    name: "SNAT Home Assistant to Xiaomi IoT"
    src_address: "192.0.2.10"
    state: absent
```

## Return Values

| Key | Type | Description |
|-----|------|-------------|
| `changed` | bool | Whether a change was applied to the controller. |
| `rule` | dict | Current state of the rule after the operation, or `null` if deleted. |
