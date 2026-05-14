# hellqvio86.unifi.unifi_switch_profile

Manage logical switch profiles.

## Description
Switch profiles are used to define a set of port overrides for specific switch models. This module manages these logical entities within your IaC.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the switch profile. |
| `model` | str | Yes | | Switch model (e.g., `USMINI`, `USW-Flex`). |
| `port_profile_overrides` | dict | No | | Map of port numbers to port profile names. |
| `state` | str | No | `present` | Whether the profile should be `present`. |

## Examples

### Define a profile for an 8-port switch
```yaml
- name: Create Switch Profile
  hellqvio86.unifi.unifi_switch_profile:
    name: "Access Switch Profile"
    model: "USMINI"
    port_profile_overrides:
      1: "WAN"
      2: "IoT"
      3: "IoT"
```
