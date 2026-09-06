# hellqvio86.unifi.unifi_dhcp_reservation

Manage DHCP fixed IP reservations on a UniFi controller

## Description
Create, update, or delete DHCP fixed IP (static) reservations for known client devices on a UniFi controller.

The client device must already be known to the controller (have connected at least once).

Uses the `/proxy/network/api/s/{site}/stat/alluser` endpoint to discover known clients and `/proxy/network/api/s/{site}/rest/user/{_id}` to apply changes.

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
| `state` | str | No | `present` | Whether the DHCP reservation should be present or absent. `present` ensures the client has a fixed IP reservation. `absent` removes the fixed IP reservation from the client. Choices: `present`, `absent`. |
| `mac` | str | Yes |  | MAC address of the client device. The client must already be known to the UniFi controller. |
| `name` | str | No |  | Friendly name to assign to the client device. If not provided, the existing name is kept. |
| `fixed_ip` | str | No |  | Static IP address to assign to the client. Required when `state=present`. |
| `network_name` | str | No |  | Name of the network (LAN) for the fixed IP reservation. If not provided, the existing network assignment is kept. |

## Examples

```yaml
- name: Ensure a DHCP reservation exists
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:01"
    name: "Example Device"
    fixed_ip: "198.51.100.71"
    network_name: "Default"

- name: Remove a DHCP reservation
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:02"
    state: absent
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether any change was applied. |
| `reservation` | dict | when state is present and client is found | The current state of the reservation after the operation. |
| `client` | dict | when client is found | The current state of the client after the operation. |
