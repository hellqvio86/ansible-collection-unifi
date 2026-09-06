# hellqvio86.unifi.unifi_switch_profile

Manage UniFi switch profiles (logical groups of port overrides)

## Description
Manage UniFi switch profiles which define a set of port-level overrides for specific switch models.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller. |
| `username` | str | No |  | UniFi controller username. |
| `password` | str | No |  | UniFi controller password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `id` | str | No |  | ID of the switch profile. |
| `state` | str | No | `present` | Whether the profile should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the switch profile. |
| `model` | str | No |  | Switch model this profile applies to (e.g., USMINI). |
| `description` | str | No |  | Description of the switch profile. |
| `port_profile_overrides` | dict | No |  | Dictionary mapping port numbers to port profile names. |

## Examples

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

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `switch_profile` | dict | always | Configuration of the switch profile. |
