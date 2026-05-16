# hellqvio86.unifi.unifi_rsyslog

Manage UniFi Remote Syslog (rsyslogd) settings.

## Description
This module configures the Remote Syslog (Activity Logging) settings for the controller and all managed devices.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled` | bool | No | `true` | Whether remote syslog is enabled. |
| `ip` | str | Yes | | IP address of the syslog server. |
| `port` | int | No | `10516` | Port of the syslog server. |
| `log_all_contents` | bool | No | `true` | Whether to log all contents. |

## Examples

### Set activity logging to a central server
```yaml
- name: Configure activity logging
  hellqvio86.unifi.unifi_rsyslog:
    ip: "192.0.2.50"
    enabled: true
```
