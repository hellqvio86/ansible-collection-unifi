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

## Authentication (The Login Step)

To avoid cluttering your tasks, use `module_defaults` to define your credentials once. This acts as your **"Login Step"**.

```yaml
- name: Manage UniFi
  hosts: localhost
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      username: "admin"
      password: "password"
```

## Usage: WiFi & Networks

```yaml
- name: Ensure Home WiFi exists
  hellqvio86.unifi.unifi_wlan:
    name: "HomeWiFi"
    passphrase: "securepassword"
    state: present
```

## Usage: Switching

```yaml
- name: Create IoT port profile
  hellqvio86.unifi.unifi_port_profile:
    name: "IoT Ports"
    native_network_name: "IoT"
    tagged_network_names: ["Camera"]

- name: Assign profile to switch
  hellqvio86.unifi.unifi_switch_profile_assignment:
    switch_name: "Main-Switch"
    profile_name: "IoT Ports"
```

## Usage: Firewall (Modern Policy Engine)

```yaml
- name: Create Internal Zone
  hellqvio86.unifi.unifi_firewall_zone:
    name: "Internal"
    networks: ["Default", "IoT"]

- name: Block IoT to Gateway
  hellqvio86.unifi.unifi_firewall_policy:
    name: "Block IoT to Gateway"
    action: BLOCK
    source: { zone: "Internal" }
    destination: { zone: "External" }
```

## Usage: System & Security

```yaml
- name: Configure activity logging
  hellqvio86.unifi.unifi_rsyslog:
    ip: "192.168.1.50"
    enabled: true

- name: Ensure admin SSH keys are present
  hellqvio86.unifi.unifi_ssh_key:
    keys: ["ssh-rsa AAAAB3Nza..."]
```

## Usage: Information Gathering

```yaml
- name: Gather all live state
  hellqvio86.unifi.unifi_info:
    gather_subset: [ wifi, firewall_groups ]
  register: unifi_state
```

## Environment Variables

You can also skip credentials entirely by setting `UNIFI_HOST`, `UNIFI_USERNAME`, and `UNIFI_PASSWORD`.

## License

[MIT](LICENSE.md)
