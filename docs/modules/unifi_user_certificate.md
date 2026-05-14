# hellqvio86.unifi.unifi_user_certificate

Manage user-facing certificates via UniFi OS API.

## Description
This module manages certificates used for user-facing services (like the Captive Portal or Radius) using the UniFi OS API.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `certificate` | str | Yes | | The certificate content (string). |
| `private_key` | str | Yes | | The private key content (string). |
| `state` | str | No | `present` | Whether the certificate should be `present`. |

## Examples

### Update Radius certificate
```yaml
- name: Update User Certificate
  hellqvio86.unifi.unifi_user_certificate:
    certificate: "{{ lookup('file', 'cert.pem') }}"
    private_key: "{{ lookup('file', 'key.pem') }}"
    state: present
```
