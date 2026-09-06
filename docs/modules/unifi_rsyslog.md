# hellqvio86.unifi.unifi_rsyslog

Manage UniFi Remote Syslog (rsyslogd) settings

## Description
Configure Remote Syslog settings in a UniFi controller.

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
| `enabled` | bool | No | `True` | Whether remote syslog is enabled. |
| `ip` | str | No |  | IP address of the syslog server. |
| `port` | int | No | `10516` | Port of the syslog server. |
| `log_all_contents` | bool | No | `True` | Whether to log all contents. |
| `debug` | bool | No | `False` | Whether to enable debug logging. |
| `netconsole_enabled` | bool | No | `False` | Whether to enable netconsole. |

## Examples

```yaml
- name: Configure activity logging
  hellqvio86.unifi.unifi_rsyslog:
    ip: "192.0.2.50"
    enabled: true
```

## Return Values

| Return Value | Type | Returned | Description |
|--------------|------|----------|-------------|
| `rsyslog` | dict | always | Current remote syslog configuration. |
