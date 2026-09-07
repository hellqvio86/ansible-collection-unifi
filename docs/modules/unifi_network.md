# hellqvio86.unifi.unifi_network

Manage networks and VLANs on a UniFi controller

## Description
Create, update, or remove networks and VLANs on a UniFi controller.

Supports corporate routed networks, isolated guest networks, and pure Layer-2 VLAN-only networks.

Configures IP subnets, VLAN IDs, DHCP server settings, DNS overrides, and network features.

Uses the official UniFi REST endpoint `/proxy/network/api/s/{site}/rest/networkconf`.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host or IP address of the UniFi controller. |
| `username` | str | No |  | UniFi controller username. |
| `password` | str | No |  | UniFi controller password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `state` | str | No | `present` | Whether the network should exist or be removed. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Name of the network or VLAN. |
| `id` | str | No |  | Unique identifier of the network for explicit ID-based targeting or renaming. |
| `purpose` | str | No | `corporate` | Network purpose / type. `corporate` is a standard internal routed network. `guest` is an isolated guest network. `vlan-only` is a Layer-2 tagged VLAN without routing or DHCP on the gateway. `wan` represents a WAN interface uplink. Choices: `corporate`, `guest`, `vlan-only`, `wan`. |
| `vlan` | int | No |  | VLAN ID (tag number) between 1 and 4094. Setting this enables VLAN tagging on the network. |
| `vlan_enabled` | bool | No |  | Explicitly enable or disable VLAN tagging. Automatically set to true if `vlan` is specified and > 1. |
| `ip_subnet` | str | No |  | Gateway IP address and CIDR prefix (e.g., `192.168.20.1/24`). Required for `corporate` and `guest` networks when `state=present`. |
| `domain_name` | str | No |  | Local domain name suffix for clients on this network (e.g., `lan.local`). |
| `enabled` | bool | No | `True` | Whether the network is enabled. |
| `dhcpd_enabled` | bool | No |  | Enable the built-in DHCP server for this network. Only applicable to `corporate` and `guest` networks. |
| `dhcp_start` | str | No |  | Start IP address for the DHCP range (e.g., `192.168.20.10`). |
| `dhcp_stop` | str | No |  | End IP address for the DHCP range (e.g., `192.168.20.200`). |
| `dhcp_lease_time` | int | No |  | DHCP lease time in seconds (e.g., 86400). |
| `dhcp_dns_1` | str | No |  | Primary DNS server IP for DHCP clients. |
| `dhcp_dns_2` | str | No |  | Secondary DNS server IP for DHCP clients. |
| `dhcp_gateway` | str | No |  | Gateway IP override distributed via DHCP. |
| `dhcp_guarding` | bool | No |  | Enable DHCP Guarding to block rogue DHCP servers. |
| `dhcp_guarding_servers` | list | No |  | List of trusted DHCP server IP addresses when DHCP guarding is enabled. |
| `igmp_snooping` | bool | No |  | Enable IGMP snooping on switches for this network. |
| `multicast_dns` | bool | No |  | Enable Multicast DNS (mDNS) reflector for this network. |
| `networkgroup` | str | No | `LAN` | Network group assignment. Choices: `LAN`, `WAN`. |

## Examples

```yaml
- name: Create a corporate VLAN network
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "IoT Network"
    purpose: "corporate"
    vlan: 20
    ip_subnet: "192.168.20.1/24"
    dhcpd_enabled: true
    dhcp_start: "192.168.20.10"
    dhcp_stop: "192.168.20.200"
    state: present

- name: Create a Layer-2 VLAN-only network for third-party router
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "CCTV VLAN"
    purpose: "vlan-only"
    vlan: 50
    state: present

- name: Remove a VLAN network
  hellqvio86.unifi.unifi_network:
    host: "192.0.2.1"
    api_key: "my-api-key"
    name: "CCTV VLAN"
    state: absent
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether the network was created, updated, or removed. |
| `network` | dict | always | Current state of the network configuration. |
