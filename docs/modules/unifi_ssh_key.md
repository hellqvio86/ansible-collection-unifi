# hellqvio86.unifi.unifi_ssh_key

Manage persistent SSH keys on UniFi OS

## Description
Registers SSH public keys in the UniFi OS system configuration.

Unlike authorized_keys, these keys persist across reboots and provisions.

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
| `keys` | list | No | `[]` | List of SSH public keys to ensure are present or absent. |
| `state` | str | No | `present` | Whether the keys should be present or absent. Choices: `present`, `absent`. |

## Examples

```yaml
- name: Register admin keys
  hellqvio86.unifi.unifi_ssh_key:
    keys:
      - "ssh-rsa AAAAB3Nza..."
      - "ssh-ed25519 AAAAC3Nza..."
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `ssh_keys` | list | always | Registered SSH keys on the controller. |
