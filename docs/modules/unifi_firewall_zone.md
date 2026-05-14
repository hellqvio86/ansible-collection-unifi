# hellqvio86.unifi.unifi_firewall_zone

Manage UniFi v8.3+ Firewall Zones.

## Description
This module manages network zones in the modern Policy Engine (v2 API). Zones allow you to group multiple networks (VLANs) together for simplified firewall policy management.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the firewall zone. |
| `state` | str | No | `present` | Whether the zone should be `present` or `absent`. |
| `networks` | list | No | | List of network names (e.g., `Default`, `IoT`) to include in this zone. |

## Examples

### Create an Internal zone grouping several networks
```yaml
- name: Ensure Internal Zone exists
  hellqvio86.unifi.unifi_firewall_zone:
    name: "Internal"
    networks:
      - "Default"
      - "IoT"
      - "Sensors"
    state: present
```
