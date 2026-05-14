# hellqvio86.unifi.unifi_wlan

Manage UniFi wireless network (WLAN) configurations.

## Description
This module manages the controller's wireless network definitions in the configured site. It allows for creating, updating, and deleting SSIDs with specific security and network settings.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | | Name of the wireless network (SSID). |
| `state` | str | No | `present` | Whether the WLAN should be `present` or `absent`. |
| `enabled` | bool | No | `true` | Enable or disable the WLAN. |
| `network_name` | str | No | | Name of the associated network profile (e.g., `Default`, `IoT`). |
| `security` | str | No | | Security mode: `open`, `wpapsk`, `wpa2`, `wpa3`. |
| `passphrase` | str | No | | WPA passphrase for secured networks. |
| `bands` | list | No | `['2g', '5g']` | Radio bands to enable: `2g`, `5g`, `6g`. |

## Examples

### Ensure a secure IoT WiFi exists
```yaml
- name: Create IoT WLAN
  hellqvio86.unifi.unifi_wlan:
    name: "IoT-Home"
    passphrase: "secure-iot-pass"
    network_name: "IoT"
    security: wpa2
    state: present
```

### Delete an old WiFi network
```yaml
- name: Remove Legacy WiFi
  hellqvio86.unifi.unifi_wlan:
    name: "Legacy-WiFi"
    state: absent
```

## Return Values
* `wlan`: The full configuration object of the created or updated wireless network.
