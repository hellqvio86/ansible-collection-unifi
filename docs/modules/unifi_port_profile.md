# hellqvio86.unifi.unifi_port_profile

Manage UniFi switch port profiles

## Description
Create, update, or delete port profiles in a UniFi controller.

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
| `id` | str | No |  | ID of the port profile. |
| `state` | str | No | `present` | Whether the profile should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the port profile. |
| `native_network_name` | str | No |  | Name of the native (untagged) network. |
| `tagged_network_names` | list | No |  | List of names of tagged networks. |
| `autoneg` | bool | No |  | Whether to enable auto-negotiation. |

## Examples

```yaml
- name: Create IoT Port Profile
  hellqvio86.unifi.unifi_port_profile:
    name: "IoT Ports"
    native_network_name: "IoT"
    tagged_network_names: ["Camera"]
    state: present
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `port_profile` | dict | always | Configuration of the port profile. |
