# UniFi Ansible Collection

[![CI](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg)](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml)
[![Tests](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg?job=test)](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml)
[![Ansible Galaxy](https://img.shields.io/ansible/collection/v/hellqvio86/unifi?logo=ansible&logoColor=black&label=Ansible%20Galaxy)](https://galaxy.ansible.com/hellqvio86/unifi)

> [!NOTE]
> **Release Status**: This collection is under active development (v0.0.x) progressing toward v0.1.0 (Beta) and v1.0.0 milestones. Core APIs and modules are thoroughly tested with strict typing, but minor breaking improvements may occur between 0.0.x minor releases per SemVer.

> [!IMPORTANT]
> **Disclaimer**: This project is an independent open-source initiative and is **not** affiliated with, sponsored by, or endorsed by Ubiquiti Inc. UniFi and Ubiquiti are trademarks of Ubiquiti Inc.

An Ansible collection for managing UniFi Network (v8.x+) and UniFi OS (v3.x+) with a focus on modern API-driven infrastructure, strict typing, idempotency, and check mode support.

## Compatibility Matrix

| Component | Supported Versions | Tested Versions | Capabilities |
| :--- | :--- | :--- | :--- |
| **UniFi Network** | **8.0.0+** (Recommended) | 8.0.28, 8.1.113, 8.2.93 | **Full**: Policy Engine v2 (`unifi_firewall_policy`, `unifi_firewall_zone`, `unifi_nat_rule`), REST modules (`unifi_network`, `unifi_device`, `unifi_wlan`, `unifi_port_profile`, `unifi_switch_profile`, `unifi_firewall_group`, `unifi_dhcp_*`, `unifi_rsyslog`) |
| **UniFi Network** | **7.0.0 - 7.5.x** | 7.4.156, 7.5.176 | **Partial**: REST modules supported. Policy Engine v2 modules unsupported. |
| **UniFi OS** | **3.0.0+** (Recommended) | 3.1.16, 3.2.12, 4.0.6 | **Full**: API Key auth (`api_key`), `unifi_user_certificate`, `unifi_ssh_key`, `unifi_ssl_config` |
| **UniFi OS** | **< 3.0.0** | 1.12.x, 2.5.x | **Legacy**: Username/password auth only. User certificates unsupported. |

See [Compatibility Guide](docs/compatibility.md) for detailed architecture, endpoint families, and version requirements.

## Included Modules

The collection provides 19 purpose-built modules across four core areas:

### 1. Network & Hardware Infrastructure
| Module | Description | Minimum Version |
| :--- | :--- | :--- |
| [`unifi_network`](docs/modules/unifi_network.md) | Manage corporate, guest, and VLAN-only networks, subnets, DHCP server options, mDNS, and IGMP snooping. | Network 7.0+ |
| [`unifi_device`](docs/modules/unifi_device.md) | Manage Access Points, Switches, and Gateways: adoption, naming, LED control, management VLAN, notes, and forget. | Network 7.0+ |
| [`unifi_wlan`](docs/modules/unifi_wlan.md) | Manage WiFi SSIDs, security (WPA2/WPA3), passphrases, band steering, and VLAN tags. | Network 7.0+ |
| [`unifi_port_profile`](docs/modules/unifi_port_profile.md) | Manage switch port profiles (native VLAN, tagged VLANs, PoE mode, link speed). | Network 7.0+ |
| [`unifi_switch_profile`](docs/modules/unifi_switch_profile.md) | Manage logical switch profiles. | Network 7.0+ |
| [`unifi_switch_profile_assignment`](docs/modules/unifi_switch_profile_assignment.md) | Assign port profiles to specific switch ports. | Network 7.0+ |
| [`unifi_dhcp_server`](docs/modules/unifi_dhcp_server.md) | Configure DHCP lease ranges, lease time, gateway, and DNS overrides per network. | Network 7.0+ |
| [`unifi_dhcp_reservation`](docs/modules/unifi_dhcp_reservation.md) | Manage static DHCP IP reservations bound to client MAC addresses. | Network 7.0+ |

### 2. Firewall, Routing & Security
| Module | Description | Minimum Version |
| :--- | :--- | :--- |
| [`unifi_firewall_zone`](docs/modules/unifi_firewall_zone.md) | Manage modern firewall security zones grouping networks. | Network 8.0+ |
| [`unifi_firewall_policy`](docs/modules/unifi_firewall_policy.md) | Manage modern firewall rules between security zones (v2 Policy API). | Network 8.0+ |
| [`unifi_firewall_group`](docs/modules/unifi_firewall_group.md) | Manage reusable IP address and port groups for firewall policies. | Network 7.0+ |
| [`unifi_nat_rule`](docs/modules/unifi_nat_rule.md) | Manage Source NAT, Destination NAT, and Masquerade rules (v2 Policy API). | Network 8.0+ |
| [`unifi_port_forward`](docs/modules/unifi_port_forward.md) | Configure classic port forwarding (DNAT) rules. | Network 7.0+ |

### 3. System & Controller Administration
| Module | Description | Minimum Version |
| :--- | :--- | :--- |
| [`unifi_system_settings`](docs/modules/unifi_system_settings.md) | Manage controller NTP, timezone, management LED, SSH access, and switch flow control/snooping. | Network 7.0+ |
| [`unifi_rsyslog`](docs/modules/unifi_rsyslog.md) | Configure remote syslog target and activity logging. | Network 7.0+ |
| [`unifi_ssh_key`](docs/modules/unifi_ssh_key.md) | Manage persistent system-level SSH public keys for controller admins. | UniFi OS 3.0+ |
| [`unifi_user_certificate`](docs/modules/unifi_user_certificate.md) | Manage user-facing TLS certificates via UniFi OS API. | UniFi OS 3.0+ |
| [`unifi_ssl_config`](docs/modules/unifi_ssl_config.md) | Deploy SSL certificates directly to the controller via SSH/SFTP. | UniFi OS / Linux |

### 4. Auditing & Fact Gathering
| Module | Description | Minimum Version |
| :--- | :--- | :--- |
| [`unifi_info`](docs/modules/unifi_info.md) | Gather comprehensive state across WiFi, networks, firewall, devices, settings, and DHCP. | Network 7.0+ |

## Installation

Install via Ansible Galaxy:
```bash
ansible-galaxy collection install hellqvio86.unifi
```

Or declare it in your `requirements.yml`:
```yaml
collections:
  - name: hellqvio86.unifi
    version: 0.0.31
```

## Authentication Precedence

The collection supports three authentication methods, evaluated in order of precedence:

1. **API Key (`api_key` / `UNIFI_API_KEY`)** — *Recommended for UniFi OS 3.x+ / Network 8.x+*  
   Token-based authentication passing the `X-API-KEY` header directly to UniFi OS. No login handshake or cookie management required.
2. **Pre-authenticated Session (`unifi_session_cookie` + `unifi_csrf_token`)**  
   Useful in high-throughput CI/CD pipelines or wrapper playbooks to eliminate repeated login requests across task boundaries.
3. **Username & Password (`username` + `password` / `UNIFI_USERNAME`, `UNIFI_PASSWORD`)**  
   Authenticates via `/api/auth/login` and automatically manages session cookies and CSRF tokens across the task lifecycle.

### Recommended Pattern: `module_defaults`

Define authentication once at the play level to keep your tasks clean:

```yaml
- name: Manage UniFi Infrastructure
  hosts: localhost
  gather_facts: false
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      api_key: "{{ unifi_api_key }}"
      site: "default"
      validate_certs: true
```

## Security & Operational Hardening

- **TLS Verification by Default**: All modules enforce `validate_certs: true` by default. To use internal or self-signed CAs securely, specify `ca_path: /path/to/cacert.pem` instead of disabling verification.
- **Secret Scrubbing**: Passphrases, API keys, private keys, and session tokens are scrubbed from return payloads, sanitized in diff mode, and omitted from `unifi_info` outputs.
- **Concurrency & Rate Limiting**: Host-scoped locking ensures playbooks targeting the same controller don't trigger HTTP 429 rate-limiting errors.

## Onboarding: Dump Current State as Source-of-Truth

The collection includes an onboarding playbook to export your current controller state to clean YAML files:

```bash
export UNIFI_HOST="192.168.1.1"
export UNIFI_API_KEY="your-api-key"

ansible-playbook playbooks/unifi_dump_all.yml
```

This populates `./unifi_dump/` with modular YAML exports:

```text
unifi_dump/
├── wifi.yml               # unifi_controller_wifi_networks
├── networks.yml           # unifi_controller_networks
├── devices.yml            # unifi_controller_devices
├── firewall_zones.yml     # unifi_controller_firewall_zones
├── firewall_policies.yml  # unifi_controller_firewall_policies
├── firewall_groups.yml    # unifi_controller_firewall_groups
├── port_forward.yml       # unifi_controller_port_forward
├── port_profiles.yml      # unifi_controller_port_profiles
├── dhcp_reservations.yml  # unifi_controller_dhcp_reservations
├── system_settings.yml    # unifi_controller_system_settings
└── rsyslog.yml            # unifi_controller_rsyslog
```

These files serve as documentation and direct input variables for your playbooks.

## Example Playbooks

Runnable playbooks are provided under [`examples/`](examples/):

- [`examples/site.yml`](examples/site.yml): End-to-end site configuration (WiFi, switching, firewall, system settings).
- [`examples/network_and_devices.yml`](examples/network_and_devices.yml): VLAN creation, AP adoption/naming, and SSID binding.
- [`examples/firewall_and_security.yml`](examples/firewall_and_security.yml): Modern firewall zones, inter-zone drop policies, and port forwards.

## Development & Testing

This project enforces strict code quality and Ansible standards via `make`:

```bash
make venv      # Set up virtualenv with all dev dependencies
make lint      # Run ruff, ansible-lint, ansible-test sanity, doc sync, version sync
make test      # Run full unit and integration test suite (249 tests)
make build     # Build collection tarball into releases/
```

## License

[MIT](LICENSE.md) — Copyright (c) 2026 Olof Hellqvist (@hellqvio86)
