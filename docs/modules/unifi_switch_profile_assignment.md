# hellqvio86.unifi.unifi_switch_profile_assignment

Assign Switch Profiles to UniFi Switches

## Description
Assign or remove switch profiles from UniFi switches.

Supports single assignment mode and batch mode.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller. |
| `username` | str | No |  | UniFi controller administrator username. |
| `password` | str | No |  | UniFi controller administrator password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `api_key` | str | No |  | Token for direct API authentication. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `state` | str | No | `present` | Whether the assignment should be present or absent. Choices: `present`, `absent`. |
| `switch_name` | str | No |  | Name of the switch to target. |
| `switch_mac` | str | No |  | MAC address of the switch. |
| `switch_ip` | str | No |  | IP address of the switch. |
| `profile_name` | str | No |  | Name of the switch profile to assign. |
| `assignments` | list | No |  | Batch input for switch profile assignments. |
| `switch_profiles` | list | No |  | Pre-fetched list of switch profiles to avoid additional API lookups. |

## Examples

```yaml
- name: Assign Access Profile
  hellqvio86.unifi.unifi_switch_profile_assignment:
    switch_name: "Main-Switch"
    profile_name: "Standard Access Profile"
    state: present
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `switch_profile_assignment` | dict | always | Details of the switch profile assignment. |
