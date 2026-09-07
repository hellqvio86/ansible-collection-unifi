# hellqvio86.unifi.unifi_login

Authenticate with a UniFi controller and return a reusable session

## Description
Authenticate against a UniFi controller and retrieve pre-authenticated session tokens.

Returns `session_cookie` and `csrf_token` that can be registered and reused across subsequent tasks or playbooks via `module_defaults` using `unifi_session_cookie` and `unifi_csrf_token`.

Prevents repeating login authentication handshakes across multiple module invocations.

Also discovers and returns available sites on the controller.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | Yes |  | The host or IP address of the UniFi controller. |
| `username` | str | Yes |  | UniFi controller administrator username. |
| `password` | str | Yes |  | UniFi controller administrator password. |
| `site` | str | No | `default` | Target UniFi site name. |
| `validate_certs` | bool | No | `True` | Verify SSL certificates. |
| `ca_path` | path | No |  | Path to CA bundle file for TLS verification. |

## Examples

```yaml
- name: Log in to UniFi controller
  hellqvio86.unifi.unifi_login:
    host: "192.168.1.1"
    username: "admin"
    password: "{{ unifi_password }}"
  register: auth

- name: Perform operations using reused session
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      unifi_session_cookie: "{{ auth.unifi_session.session_cookie }}"
      unifi_csrf_token: "{{ auth.unifi_session.csrf_token }}"
      site: "{{ auth.unifi_session.site }}"
  block:
    - name: Ensure WiFi SSID exists
      hellqvio86.unifi.unifi_wlan:
        name: "GuestWiFi"
        state: present
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `changed` | bool | always | Always false since login does not mutate controller configuration. |
| `unifi_session` | dict | always | Reusable session tokens and controller metadata. |
