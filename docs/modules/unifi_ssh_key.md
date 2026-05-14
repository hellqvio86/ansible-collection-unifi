# hellqvio86.unifi.unifi_ssh_key

Manage system-level SSH keys for persistent access.

## Description
This module registers public SSH keys in the UniFi OS system configuration. This ensures that your keys persist across reboots and device provisions.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keys` | list | Yes | | List of public SSH keys (strings) to ensure are present. |

## Examples

### Ensure admin keys are present
```yaml
- name: Register admin keys
  hellqvio86.unifi.unifi_ssh_key:
    keys:
      - "ssh-rsa AAAAB3Nza..."
      - "ssh-ed25519 AAAAC3Nza..."
```
