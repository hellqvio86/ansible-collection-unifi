# hellqvio86.unifi.unifi_firewall_policy

Manage UniFi v8.3+ Policy Engine Firewall Rules.

## Description
This module targets the modern Policy Engine (v2 API) introduced in UniFi Network 8.x. It allows for zone-based firewalling which is significantly more powerful than legacy rules.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the firewall policy. |
| `action` | str | No | `ALLOW` | Action: `ALLOW`, `BLOCK`, `REJECT`, `ISOLATE`. |
| `protocol` | str | No | `all` | Protocol: `all`, `tcp`, `udp`, `icmp`, etc. |
| `index` | int | No | `10000` | Rule order (lower numbers run first). |
| `source` | dict | No | | Source config (see below). |
| `destination` | dict | No | | Destination config (see below). |

### Source/Destination Sub-options
* `zone`: Name of the zone (e.g., `Internal`, `External`, `Guest`).
* `matching_target`: `ANY`, `IP`, `NETWORK`, `DOMAIN`.
* `ips`: List of IPs or networks if matching target is not `ANY`.
* `port`: Specific port or port range.

## Examples

### Block IoT to Gateway
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
