# hellqvio86.unifi.unifi_user_certificate

Manage UniFi OS user certificates via control-plane API

## Description
Uploads and manages certificates in UniFi OS at /api/userCertificates.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | No |  | The host of the UniFi controller. |
| `username` | str | No |  | UniFi controller administrator username. |
| `password` | str | No |  | UniFi controller administrator password. |
| `site` | str | No | `default` | UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `api_key` | str | No |  | Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+). Preferred over username/password. Can also be set via the `UNIFI_API_KEY` or `UNIFI_API_TOKEN` environment variables. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |
| `unifi_session_cookie` | str | No |  | Pre-authenticated session cookie string. |
| `unifi_csrf_token` | str | No |  | Pre-authenticated CSRF token. |
| `state` | str | No | `present` | Whether the user certificate should be present or absent. Choices: `present`, `absent`. |
| `name` | str | Yes |  | Friendly name of the user certificate. |
| `id` | str | No |  | ID of the user certificate. |
| `cert` | str | No |  | The PEM-encoded certificate string. |
| `key` | str | No |  | The PEM-encoded private key string. |
| `active` | bool | No | `True` | Whether the certificate is marked active. |

## Examples

```yaml
- name: Update User Certificate
  hellqvio86.unifi.unifi_user_certificate:
    certificate: "{{ lookup('file', 'cert.pem') }}"
    private_key: "{{ lookup('file', 'key.pem') }}"
    state: present
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `certificate` | dict | always | Details of the updated user certificate. |
