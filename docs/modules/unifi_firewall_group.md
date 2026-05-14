# hellqvio86.unifi.unifi_firewall_group

Manage UniFi Firewall Groups (IP and Port lists).

## Description
This module manages legacy REST-based firewall groups. These groups can be used in both legacy firewall rules and the modern Policy Engine.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the group. |
| `state` | str | No | `present` | Whether the group should be `present` or `absent`. |
| `type` | str | No | `address_group` | Type of group: `address_group`, `ipv6_address_group`, `port_group`. |
| `members` | list | Yes | | List of members (IPs, CIDRs, or Ports). |

## Examples

### Create an address group for blocklisting
```yaml
- name: Create Malicious IPs group
  hellqvio86.unifi.unifi_firewall_group:
    name: "Malicious IPs"
    type: address_group
    members:
      - "1.2.3.4"
      - "8.8.8.8/32"
    state: present
```

### Create a port group for web services
```yaml
- name: Create Web Ports group
  hellqvio86.unifi.unifi_firewall_group:
    name: "Web Ports"
    type: port_group
    members: ["80", "443", "8080"]
```
