# hellqvio86.unifi.unifi_dhcp_server

Manage DHCP server settings on a UniFi network

## Description
Configure DHCP server settings (range, lease time, DNS, gateway) for a network on a UniFi controller.

Uses the `/proxy/network/api/s/{site}/rest/networkconf` endpoint to manage DHCP settings per network.

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
| `id` | str | No |  | ID of the network configuration. |
| `state` | str | No | `present` | Whether DHCP server should be configured or disabled on the network. `present` ensures DHCP settings are applied. `absent` disables the DHCP server on the network. Choices: `present`, `absent`. |
| `network` | str | Yes |  | Name of the network (LAN) to configure DHCP on. |
| `enabled` | bool | No | `True` | Whether the DHCP server is enabled on this network. When `state=absent`, this is forced to `false`. |
| `dhcp_start` | str | No |  | Start IP address of the DHCP range (e.g., `192.168.1.100`). Required when `enabled=true` and `state=present`. |
| `dhcp_stop` | str | No |  | End IP address of the DHCP range (e.g., `192.168.1.200`). Required when `enabled=true` and `state=present`. |
| `lease_time` | int | No |  | DHCP lease time in seconds. |
| `dns_1` | str | No |  | Primary DNS server IP address. |
| `dns_2` | str | No |  | Secondary DNS server IP address. |
| `gateway` | str | No |  | Gateway IP address override. If not set, the network's configured gateway is used. |
| `domain` | str | No |  | DHCP domain name (e.g., `lan.example.com`). |

## Examples

```yaml
- name: Configure DHCP server on the Default network
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Default"
    enabled: true
    dhcp_start: "192.168.1.100"
    dhcp_stop: "192.168.1.200"
    lease_time: 86400
    dns_1: "192.168.1.1"
    dns_2: "8.8.8.8"

- name: Disable DHCP server on a network
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Guest"
    state: absent

- name: Update DNS servers only
  hellqvio86.unifi.unifi_dhcp_server:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    network: "Default"
    enabled: true
    dns_1: "1.1.1.1"
    dns_2: "8.8.8.8"
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether any change was applied. |
| `network` | dict | always | The current state of the network configuration after the operation. |
