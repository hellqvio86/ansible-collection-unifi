# hellqvio86.unifi.unifi_ssl_config

Deploy SSL certificates to UniFi OS via modulated SSH.

## Description
This module deploys SSL certificates (e.g., Let's Encrypt wildcards) to the UniFi OS system. It uses an SSH-modulated transport to update the underlying system files and restart the UI service.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cert_path` | str | Yes | | Local path to the fullchain certificate (PEM). |
| `key_path` | str | Yes | | Local path to the private key (PEM). |
| `remote_host` | str | No | | Optional remote host if different from the API host. |

## Examples

### Deploy a new certificate
```yaml
- name: Update UDM SSL Certificate
  hellqvio86.unifi.unifi_ssl_config:
    cert_path: "/etc/letsencrypt/live/unifi.example.com/fullchain.pem"
    key_path: "/etc/letsencrypt/live/unifi.example.com/privkey.pem"
```
