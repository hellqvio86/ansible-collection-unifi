# Changelog

## 0.0.6

### New Features
- **Session Reuse**: All modules now accept `unifi_session_cookie` and `unifi_csrf_token` parameters to reuse an existing authentication session, avoiding UniFi rate limits (HTTP 429) when running loops over many items.
- **Role Login Task**: Added `login.yml` that authenticates once and shares the session across all subsequent module calls in the playbook.
- **`unifi_info` Subnet Fallback**: DHCP reservations without an explicit `network_id` are now resolved by matching `fixed_ip` against network subnets.

### Improvements
- **Modules**: Added `unifi_session_cookie`/`unifi_csrf_token` params to all 11 API-based modules.

## 0.0.5

### New Modules
- `unifi_rsyslog`: Configure remote syslog (Activity Logging) settings.
- `unifi_info`: Gather comprehensive infrastructure state (WiFi networks, firewall groups, zones, policies, switch profiles, and more).

### Improvements
- **Security**: Fixed SSH host key verification in `unifi_ssl_config` and `unifi_user_certificate` to reject unknown hosts (previously accepted all).
- **Documentation**: Added full per-module reference docs under `docs/modules/` for all 11 modules.
- **Documentation**: Added `docs/authentication.md` guide and restructured README with clear examples.
- **Packaging**: Added `Makefile` with `build`, `publish`, `test`, `lint`, and `format` targets.
- **Packaging**: Configured `build_ignore` in `galaxy.yml` to produce a lean distribution artifact.
- **Release Automation**: Added CI/CD workflow that creates a draft GitHub release on version bump and publishes to Ansible Galaxy when the release is published.
- **Dependencies**: Bumped `paramiko>=5.0.0` and `cryptography>=48.0.0`.
- **Linting**: All modules now pass `ruff` and `ansible-lint` with zero errors.
- **Testing**: Fixed unit test assertions for `unifi_firewall_policy` and `unifi_switch_profile_assignment` to match updated module return structures.
- **Governance**: Added `agents.md` documenting development standards and restrictions.

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
