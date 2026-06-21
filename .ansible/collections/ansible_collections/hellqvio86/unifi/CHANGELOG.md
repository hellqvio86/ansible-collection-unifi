# Changelog

## 0.0.18

### New Features
- **`unifi_user_certificate`**: Match certs by fingerprint and use unique names for new uploads to prevent duplicates.

### Dependencies
- **`deps`**: Update cryptography requirement from >=48.0.1 to >=49.0.0.
- **`deps`**: Update cryptography requirement from >=48.0.0 to >=48.0.1.

### Test Coverage
- Update unifi_user_certificate unit tests for fingerprint matching.

### CI/CD
- Dynamically extract current version notes from CHANGELOG.md for draft release.

### Other Changes
- Sort imports, update manifest, and add unit test updates.
## 0.0.16

### Bug Fixes
- **`unifi_firewall_zone`**: Skip `PUT` requests on zone update as the endpoint does not support them (resulting in 500 errors). Exclude unsupported `type` parameter from the `POST` creation payload, and include the mandatory empty `network_ids` list.
- **`unifi_api`**: Extended `fetch_url` timeout to 30 seconds to prevent timeouts during large controller state requests.
- **Test Suite**: Updated firewall zone unit tests to align with the payload structure and skip zone update PUT calls.

## 0.0.15

### Bug Fixes
- **`unifi_firewall_zone`**: Restrict PUT request payload to `name` and `description` to prevent API errors on update.
- **`unifi_port_profile`**: Updated to support the modern UniFi controller API by utilizing `tagged_vlan_mgmt="custom"`, `forward="customize"`, and calculating `excluded_networkconf_ids` from networks.
- **`unifi_switch_profile_assignment`**: Automatically clean up conflicting network configuration keys in port overrides.
- **`unifi_wlan`**: Added `band` configuration parameter (`both`, `2g`, `5g`) and clone existing `ap_group_ids` when creating new WLANs.
- **Test Suite**: Fixed and enhanced unit tests for `unifi_port_profile` and `unifi_wlan` modules using pytest.

## 0.0.14

### Bug Fixes
- **Port Overrides**: Fix PoE mode preservation for port overrides.
- **`unifi_switch_profile`**: Handle unsupported switch profile API configurations gracefully.
- **Test Suite**: Added additional unit tests.

## 0.0.13

### Improvements
- **`unifi_api`**: Serialize UniFi API requests using file locks (`/tmp/ansible_unifi_api.lock`) to prevent HTTP 429 rate limits during concurrent execution.

## 0.0.12

### Bug Fixes
- **`unifi_info`**: Added devices endpoint compatibility fallback from `/rest/device` to `/stat/device` when controllers return `404` on the REST path.

## 0.0.11

### Improvements
- **`unifi_info`**: Fail fast on API request errors instead of silently returning partial subset data.
- **`unifi_api`**: Added retry/backoff handling for `429` and session refresh/relogin retry flow for `401`/`403`.
- **`unifi_dhcp_reservation`**: Added explicit failure on network fetch errors and normalized `before`/`after`/`diff` return fields.
- **Onboarding**: Added bundled `playbooks/unifi_dump_all.yml` and aligned docs to use shipped playbook path.
- **Licensing**: Standardized module headers to MIT to match collection metadata.

## 0.0.10

### Bug Fixes
- **`unifi_firewall_group`**: Fixed `TypeError` crash when `group_members` is `None` (state=absent).
- **`unifi_ssl_config`**: Fixed `AttributeError` crash when `cert_content` or `key_content` is `None`.
- **`unifi_switch_profile`**: Replaced no-op stub with full CRUD implementation (create, update, delete switch profiles).

### Improvements
- **`unifi_info`**: Added unit test coverage for `system_settings` and `port_forward` subsets.
- **Test Coverage**: Added 6 new test files covering previously untested modules: `unifi_wlan`, `unifi_info`, `unifi_rsyslog`, `unifi_firewall_zone`, `unifi_firewall_group`, `unifi_user_certificate`.
- **Docs**: Fixed inaccurate `required: true` annotations for `host`/`username`/`password` in `unifi_wlan` and `unifi_switch_profile_assignment`.

## 0.0.9

### New Modules
- `unifi_port_forward`: Manage port forwarding rules.

### Improvements
- **`unifi_info`**: Added `port_forward` gather subset that exports port forwarding rules.

## 0.0.8

### New Modules
- `unifi_system_settings`: Configure system-wide NTP servers, timezone, and management settings (LED, SSH).

### Improvements
- **`unifi_info`**: Added `system_settings` gather subset that exports NTP, timezone, and management (LED, SSH) settings.

## 0.0.7

### New Modules
- `unifi_dhcp_server`: Configure DHCP server settings (range, lease time, DNS, gateway) per network.

### Improvements
- **`unifi_info`**: Added `networks` gather subset that exports DHCP configuration (enabled, range, lease, DNS, gateway, domain) per network.

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
