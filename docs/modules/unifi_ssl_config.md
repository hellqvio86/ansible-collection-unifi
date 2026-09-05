# hellqvio86.unifi.unifi_ssl_config

Deploy SSL certificates to UniFi OS via SSH (Privileged Escape Hatch).

## Description

> [!WARNING]
> This is a **privileged escape hatch module**, not a standard UniFi REST API integration. It requires root SSH access to the UniFi OS host and interacts directly with internal filesystem paths (`/data/unifi-core/config/`) and restarts the `unifi-core` service.

This module deploys custom SSL certificates (such as Let's Encrypt certificates) directly to the UniFi OS filesystem. Before touching the remote host, it cryptographically validates:
- PEM syntax and structure for certificates and private keys.
- That the certificate public key strictly matches the private key (supports RSA, ECDSA, Ed25519).
- Certificate validity dates (rejects expired or not-yet-valid certificates; warns on impending expiry).
- Certificate chain consistency when multiple certificates are present in `cert_content`.

File deployment is transactionally safe using POSIX atomic renames with automatic backup-before-replace and rollback to ensure existing known-good certificates are never lost.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | Yes | | IP address or hostname of the UniFi OS console (UDM, UDR, UCG, UXG). |
| `ssh_username` | str | No | `root` | SSH username. |
| `ssh_password` | str | No | | SSH password (sensitive, `no_log`). |
| `ssh_key` | str | No | | Path to SSH private key file. |
| `cert_content` | str | No | | Content of the certificate or fullchain in PEM format (`no_log`). |
| `key_content` | str | No | | Content of the private key in PEM format (`no_log`). |
| `cert_path` | str | No | `/data/unifi-core/config/unifi-core.crt` | Target path for the certificate on the UniFi OS host. |
| `key_path` | str | No | `/data/unifi-core/config/unifi-core.key` | Target path for the private key on the UniFi OS host. |
| `restart_service` | bool | No | `true` | Whether to restart `service_name` after updating files. |
| `service_name` | str | No | `unifi-core` | Systemd service to restart. |
| `timeout` | int | No | `30` | SSH connection timeout in seconds. |
| `operation_timeout` | int | No | `30` | SFTP and command execution timeout in seconds. |
| `host_key_policy` | str | No | `reject` | Host key verification policy: `reject` (strict known_hosts verification), `auto_add`, or `warning`. |
| `warning_days` | int | No | `30` | Number of days before certificate expiry to issue an Ansible warning. |

## Examples

### Deploy a new Let's Encrypt certificate
```yaml
- name: Deploy custom SSL certificate to UDM Pro
  hellqvio86.unifi.unifi_ssl_config:
    host: "192.168.1.1"
    ssh_username: "root"
    ssh_key: "~/.ssh/id_ed25519"
    cert_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/fullchain.pem') }}"
    key_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/privkey.pem') }}"
    host_key_policy: "reject"
```
