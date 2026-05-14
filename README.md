# UniFi Ansible Collection

![CI](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/hellqvio86/ansible-collection-unifi)

> [!CAUTION]
> **Alpha Status**: This collection is currently in early alpha. APIs and module arguments are subject to breaking changes. Use with caution in production environments.

> [!IMPORTANT]
> **Disclaimer**: This project is an independent open-source initiative and is **not** affiliated with, sponsored by, or endorsed by Ubiquiti Inc. UniFi and Ubiquiti are trademarks of Ubiquiti Inc.

An Ansible collection for managing UniFi Network (v8.x+) and UniFi OS (v3.x+) with a focus on modern API-driven infrastructure.

## Features

- **Zone-Based Firewall Management**: Uses the modern Policy Engine (v2 API) for fine-grained traffic control.
- **Persistent SSH Keys**: Registers public keys in the UniFi OS system configuration so they persist across reboots and provisions.
- **Automated SSL Deployment**: Simplifies the deployment of Let's Encrypt or other custom wildcard certificates.
- **Centralized Authentication**: Shared API utility handles JWT and CSRF token complexity automatically.

## Included Modules

### Network Management
- `hellqvio86.unifi.unifi_wlan`: Manage WiFi networks and passphrases.
- `hellqvio86.unifi.unifi_port_profile`: Manage switch port profiles (VLAN, PoE, speed).
- `hellqvio86.unifi.unifi_switch_profile`: Manage logical switch profiles.
- `hellqvio86.unifi.unifi_switch_profile_assignment`: Assign profiles to specific switches.

### Firewall & Security
- `hellqvio86.unifi.unifi_firewall_policy`: Manage modern firewall rules (v2 API).
- `hellqvio86.unifi.unifi_firewall_zone`: Manage firewall zones (v2 API).
- `hellqvio86.unifi.unifi_firewall_group`: Manage IP and Port groups (REST API).

### System & Settings
- `hellqvio86.unifi.unifi_rsyslog`: Configure remote syslog (Activity Logging) settings.
- `hellqvio86.unifi.unifi_ssh_key`: Manage system-level SSH keys for persistent access.
- `hellqvio86.unifi.unifi_ssl_config`: Deploy SSL certificates via modulated SSH.
- `hellqvio86.unifi.unifi_user_certificate`: Manage user-facing certificates via UniFi OS API.

## Requirements

- Python >= 3.10
- `PyJWT` (for token handling)
- `paramiko` (for SSH-modulated tasks)

## Installation

```bash
ansible-galaxy collection install hellqvio86.unifi
```

## Example Usage

### Managing WiFi Networks

```yaml
- name: Ensure Home WiFi exists
  hellqvio86.unifi.unifi_wlan:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    name: "HomeWiFi"
    passphrase: "securepassword"
    network: "Default"
    bands: ["2g", "5g"]
    state: present
```

### Managing Remote Syslog

```yaml
- name: Configure activity logging
  hellqvio86.unifi.unifi_rsyslog:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    ip: "192.168.1.50"
    enabled: true
```

### Managing SSH Keys

```yaml
- name: Ensure admin keys are present
  hellqvio86.unifi.unifi_ssh_key:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    keys:
      - "ssh-rsa AAAAB3Nza..."
```

## License

[MIT](LICENSE.md)
