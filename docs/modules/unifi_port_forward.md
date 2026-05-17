# hellqvio86.unifi.unifi_port_forward

Manage UniFi port forwarding rules.

## Description
This module creates, updates, or deletes port forwarding rules on a UniFi controller.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the port forwarding rule. |
| `state` | str | No | `present` | Whether the rule should be `present` or `absent`. |
| `enabled` | bool | No | `true` | Whether the rule is enabled. |
| `protocol` | str | No | `tcp_udp` | IP protocol: `tcp`, `udp`, or `tcp_udp`. |
| `src` | str | No | `""` | Source IP or CIDR. Empty matches any. |
| `dst_port` | str | Yes | | Destination port on the WAN interface. |
| `fwd_port` | str | No | | Port to forward to on the internal host. Defaults to `dst_port`. |
| `fwd_ip` | str | Yes | | IP address of the internal host. |
| `fwd_network` | str | No | | Name of the network the internal host is on. |
| `log` | bool | No | `false` | Whether to log forwarded connections. |

## Examples

### Create SSH port forward on non-standard port
```yaml
- name: SSH to Server on port 2222
  hellqvio86.unifi.unifi_port_forward:
    name: "SSH to Server"
    enabled: true
    protocol: tcp
    dst_port: "2222"
    fwd_port: "22"
    fwd_ip: "192.168.1.10"
```

### Disable a rule
```yaml
- name: Disable SSH forward
  hellqvio86.unifi.unifi_port_forward:
    name: "SSH to Server"
    enabled: false
```

### Delete a rule
```yaml
- name: Remove old SSH forward
  hellqvio86.unifi.unifi_port_forward:
    name: "Old SSH Rule"
    state: absent
```
