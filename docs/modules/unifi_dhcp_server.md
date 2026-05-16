# unifi_dhcp_server

Manage DHCP server settings on a UniFi network.

## Synopsis

Configure DHCP server settings (range, lease time, DNS, gateway) for a network on a UniFi controller. Uses the `/proxy/network/api/s/{site}/rest/networkconf` endpoint to manage DHCP settings per network.

## Parameters

| Parameter     | Type | Required | Default | Description |
|---------------|------|----------|---------|-------------|
| `host`        | str  | no       |         | UniFi controller host |
| `username`    | str  | no       |         | UniFi controller username |
| `password`    | str  | no       |         | UniFi controller password |
| `site`        | str  | no       | default | UniFi site name |
| `validate_certs` | bool | no    | false   | Verify SSL certificates |
| `state`       | str  | no       | present | Whether DHCP server should be configured (`present`) or disabled (`absent`) |
| `network`     | str  | yes      |         | Name of the network (LAN) to configure DHCP on |
| `enabled`     | bool | no       | true    | Whether the DHCP server is enabled |
| `dhcp_start`  | str  | no       |         | Start IP of the DHCP range (required when enabled) |
| `dhcp_stop`   | str  | no       |         | End IP of the DHCP range (required when enabled) |
| `lease_time`  | int  | no       |         | DHCP lease time in seconds |
| `dns_1`       | str  | no       |         | Primary DNS server |
| `dns_2`       | str  | no       |         | Secondary DNS server |
| `gateway`     | str  | no       |         | Gateway IP override |
| `domain`      | str  | no       |         | DHCP domain name |

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

| Key | Type | Description |
|-----|------|-------------|
| `changed` | bool | Whether any change was applied |
| `network` | dict | The current state of the network configuration after the operation |
