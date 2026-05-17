# hellqvio86.unifi.unifi_system_settings

Manage UniFi system-wide settings (NTP, timezone, management).

## Description
This module configures system-wide NTP servers, timezone, management (LED, SSH) settings on a UniFi controller.

## Parameters

### ntp

| Sub-parameter | Type | Description |
|---|---|---|
| `ntp.server_1` | str | Primary NTP server. |
| `ntp.server_2` | str | Secondary NTP server. |
| `ntp.server_3` | str | Tertiary NTP server. |
| `ntp.server_4` | str | Quaternary NTP server. |
| `ntp.timezone` | str | Timezone string (e.g., `Europe/Stockholm`). |

### mgmt

| Sub-parameter | Type | Description |
|---|---|---|
| `mgmt.led_enabled` | bool | Whether device LEDs are enabled globally. |
| `mgmt.ssh_password_enabled` | bool | Whether SSH password authentication is enabled. |
| `mgmt.ssh_bind_wildcard` | bool | Whether SSH binds to all interfaces (0.0.0.0). |

## Examples

### Configure NTP servers and timezone
```yaml
- name: Set NTP and timezone
  hellqvio86.unifi.unifi_system_settings:
    ntp:
      server_1: "0.pool.ntp.org"
      server_2: "1.pool.ntp.org"
      timezone: "Europe/Stockholm"
```

### Disable device LEDs
```yaml
- name: Turn off LEDs
  hellqvio86.unifi.unifi_system_settings:
    mgmt:
      led_enabled: false
```

### Disable SSH password auth
```yaml
- name: Disable SSH password login
  hellqvio86.unifi.unifi_system_settings:
    mgmt:
      ssh_password_enabled: false
```
