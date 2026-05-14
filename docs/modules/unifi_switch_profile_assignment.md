# hellqvio86.unifi.unifi_switch_profile_assignment

Assign switch profiles to UniFi switches.

## Description
This module assigns a switch-wide profile (which defines port-level overrides) to a specific switch.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `switch_name` | str | No | | Name of the switch to target. |
| `switch_mac` | str | No | | MAC address of the switch. |
| `switch_ip` | str | No | | IP address of the switch. |
| `profile_name` | str | Yes | | Name of the switch profile to assign. |
| `state` | str | No | `present` | Whether the assignment should be `present` or `absent`. |

## Examples

### Assign a profile to a switch by its name
```yaml
- name: Assign Access Profile
  hellqvio86.unifi.unifi_switch_profile_assignment:
    switch_name: "Main-Switch"
    profile_name: "Standard Access Profile"
    state: present
```
