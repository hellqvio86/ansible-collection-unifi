# Changelog

## 0.0.3

- Added `unifi_wlan` for WiFi network management.
- Added `unifi_firewall_group` for IP and Port group management.
- Added `unifi_firewall_zone` (v2 API) for network segmentation.
- Refactored `UnifiAPI` utility for improved robustness and consistent response handling.
- Unified response parsing across all modules using `as_list()` helper.

## 0.0.2

- Added switch profile management (`unifi_switch_profile`)
- Added switch profile assignment (`unifi_switch_profile_assignment`)
- Added port profile management (`unifi_port_profile`)

## 0.0.1

- Initial release
- Modern firewall policy management (v2 API)
- Persistent SSH key management
- SSH-modulated SSL certificate deployment
