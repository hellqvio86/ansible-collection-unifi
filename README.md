# UniFi Ansible Collection

![CI](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/hellqvio86/ansible-collection-unifi)

> [!CAUTION]
> **Alpha Status**: This collection is currently in early alpha. APIs and module arguments are subject to breaking changes. Use with caution in production environments.

> [!IMPORTANT]
> **Disclaimer**: This project is an independent open-source initiative and is **not** affiliated with, sponsored by, or endorsed by Ubiquiti Inc. UniFi and Ubiquiti are trademarks of Ubiquiti Inc.

An Ansible collection for managing UniFi Network (v8.x+) and UniFi OS (v3.x+) with a focus on modern API-driven infrastructure.

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
- `hellqvio86.unifi.unifi_info`: Gather comprehensive infrastructure state.

## Installation

```bash
ansible-galaxy collection install hellqvio86.unifi
```

## Example Usage (The Clean Way)

To avoid cluttering your tasks with credentials, use `module_defaults`. This acts as your **"Login Step"**, applying the host and credentials to all modules in the collection automatically.

```yaml
- name: Manage UniFi Infrastructure
  hosts: localhost
  connection: local
  
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      username: "admin"
      password: "password"
      validate_certs: false

  tasks:
    - name: Ensure Home WiFi exists
      hellqvio86.unifi.unifi_wlan:
        name: "HomeWiFi"
        passphrase: "securepassword"
        state: present

    - name: Configure activity logging
      hellqvio86.unifi.unifi_rsyslog:
        ip: "192.168.1.50"
        enabled: true

    - name: Ensure admin SSH keys are present
      hellqvio86.unifi.unifi_ssh_key:
        keys:
          - "ssh-rsa AAAAB3Nza..."

    - name: Gather all live state
      hellqvio86.unifi.unifi_info:
        gather_subset: [ wifi, firewall_groups, rsyslog ]
      register: unifi_state
```

## Environment Variables

Alternatively, you can skip credentials in your playbooks entirely by setting these environment variables:

* `UNIFI_HOST`
* `UNIFI_USERNAME`
* `UNIFI_PASSWORD`
* `UNIFI_VALIDATE_CERTS`

## License

[MIT](LICENSE.md)
