# hellqvio86.unifi.unifi_port_forward

Manage UniFi port forwarding rules

## Description
Create, update, or delete port forwarding rules on a UniFi controller.

Uses the `/proxy/network/api/s/{site}/rest/portforward` endpoint.

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
| `id` | str | No |  | ID of the port forwarding rule. |
| `state` | str | No | `present` | Whether the rule should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the port forwarding rule. |
| `enabled` | bool | No | `True` | Whether the rule is enabled. |
| `protocol` | str | No | `tcp_udp` | IP protocol to match. Choices: `tcp`, `udp`, `tcp_udp`. |
| `src` | str | No | `` | Source IP or CIDR to match. Empty string matches any source. |
| `dst_port` | str | Yes |  | Destination port on the WAN interface (e.g., `2222`). |
| `fwd_port` | str | No |  | Port to forward traffic to on the internal host. If not set, defaults to the value of `dst_port`. |
| `fwd_ip` | str | Yes |  | IP address of the internal host to forward to. |
| `fwd_network` | str | No |  | Name of the network the internal host is on. If not set, the rule applies to the Default network. |
| `log` | bool | No | `False` | Whether to log forwarded connections. |

## Examples

```yaml
- name: Create SSH port forward on non-standard port
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "SSH to Server"
    enabled: true
    protocol: tcp
    dst_port: "2222"
    fwd_port: "22"
    fwd_ip: "192.168.1.10"
    fwd_network: "Default"

- name: Disable a port forward rule
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "SSH to Server"
    enabled: false

- name: Delete a port forward rule
  hellqvio86.unifi.unifi_port_forward:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    name: "Old Rule"
    state: absent
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether any change was applied. |
| `rule` | dict | always | The current state of the port forwarding rule after the operation. |
