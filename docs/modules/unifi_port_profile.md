# hellqvio86.unifi.unifi_port_profile

Manage UniFi switch port profiles.

## Description
This module manages port profiles which define VLAN tagging, PoE settings, and link speed for switch ports.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the port profile. |
| `state` | str | No | `present` | Whether the profile should be `present` or `absent`. |
| `native_network_name` | str | No | | Name of the untagged network. |
| `tagged_network_names` | list | No | | List of names of tagged networks. |
| `autoneg` | bool | No | | Whether to enable auto-negotiation. |

## Examples

### Create a profile for IoT devices
```yaml
- name: Create IoT Port Profile
  hellqvio86.unifi.unifi_port_profile:
    name: "IoT Ports"
    native_network_name: "IoT"
    tagged_network_names: ["Camera"]
    state: present
```
