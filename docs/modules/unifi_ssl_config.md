# hellqvio86.unifi.unifi_ssl_config

Manage UniFi OS SSL certificates via SSH (privileged escape hatch)

## Description
Privileged escape hatch module that deploys SSL certificates (CRT and KEY) directly to UniFi OS filesystem paths (/data/unifi-core/config) and restarts the unifi-core service.

Operates directly over SSH and SFTP rather than using the official UniFi REST API.

Validates PEM syntax, certificate validity dates, certificate chains, and verifies that the certificate public key cryptographically matches the private key before making any remote changes.

Employs transactional file replacement with rollback safeguards so existing certificates are never lost.

Verifies file permissions and content on the remote filesystem prior to restarting the service.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The IP or hostname of the UniFi OS console (UDM, UDR, UCG, UXG). |
| `ssh_username` | str | No | `root` | SSH username (typically root). |
| `ssh_password` | str | No |  | SSH password. |
| `ssh_key` | str | No |  | Path to SSH private key. |
| `cert_content` | str | No |  | Content of the certificate or fullchain (PEM format). |
| `key_content` | str | No |  | Content of the private key (PEM format). |
| `cert_path` | str | No | `/data/unifi-core/config/unifi-core.crt` | Target path for the certificate on the UniFi OS filesystem. |
| `key_path` | str | No | `/data/unifi-core/config/unifi-core.key` | Target path for the private key on the UniFi OS filesystem. |
| `restart_service` | bool | No | `True` | Whether to restart the UniFi OS service after certificate update. |
| `service_name` | str | No | `unifi-core` | Systemd service name to restart on UniFi OS. |
| `timeout` | int | No | `30` | SSH connection timeout in seconds. |
| `operation_timeout` | int | No | `30` | SFTP and command execution timeout in seconds. |
| `host_key_policy` | str | No | `reject` | SSH host key verification policy. `reject` requires the host key to be in known_hosts (recommended). `auto_add` automatically accepts and saves unknown host keys. `warning` logs a warning for unknown host keys but connects. Choices: `reject`, `auto_add`, `warning`. |
| `warning_days` | int | No | `30` | Number of days before certificate expiry to issue an Ansible warning. |

## Examples

```yaml
- name: Deploy custom SSL certificate to UDM Pro via SSH
  hellqvio86.unifi.unifi_ssl_config:
    host: 192.168.1.1
    ssh_username: root
    ssh_key: ~/.ssh/id_ed25519
    cert_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/fullchain.pem') }}"
    key_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/privkey.pem') }}"
    host_key_policy: reject
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Whether any certificate or key files were modified. |
| `warnings` | list | when warnings exist | Warnings related to certificate expiration or configuration. |
