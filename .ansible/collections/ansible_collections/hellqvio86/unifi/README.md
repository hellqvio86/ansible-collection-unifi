# UniFi Ansible Collection

[![CI](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg)](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml)
[![Tests](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml/badge.svg?job=test)](https://github.com/hellqvio86/ansible-collection-unifi/actions/workflows/ci.yml)
[![Ansible Galaxy](https://img.shields.io/ansible/collection/v/hellqvio86/unifi?logo=ansible&logoColor=black&label=Ansible%20Galaxy)](https://galaxy.ansible.com/hellqvio86/unifi)

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

Install via Ansible Galaxy:
```bash
ansible-galaxy collection install hellqvio86.unifi
```

Or include it in your `requirements.yml`:
```yaml
collections:
  - name: hellqvio86.unifi
    version: 0.0.10
```

## Getting Started: Dump Your Current State

Start by dumping your existing UniFi configuration. This gives you a reference of everything currently on your controller:

```bash
export UNIFI_HOST="192.0.2.1"
export UNIFI_USERNAME="admin"
export UNIFI_PASSWORD="password"

ansible-playbook hellqvio86.unifi.unifi_dump_all.yml
# or, if you have the source repo:
# ansible-playbook unifi_dump_all.yml
```

This generates a `unifi_dump/` directory with one YAML file per category (wifi, networks, firewall, DHCP, etc.). Use these files as a reference to build your playbooks and group_vars.

**Onboarding workflow:**
1. **Dump** your current state with `unifi_dump_all.yml`
2. **Review** the dumped YAML files to understand your setup
3. **Write** playbooks using the modules listed below
4. **Apply** changes gradually with ansible-pull or a management playbook

## Authentication (The Login Step)

To avoid cluttering your tasks, use `module_defaults` to define your credentials once. This acts as your **"Login Step"**.

```yaml
- name: Manage UniFi
  hosts: localhost
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.0.2.1"
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
    ip: "192.0.2.50"
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

## Development & Building

This project uses a `Makefile` to handle local development, testing, and packaging for Ansible Galaxy. Here are the available commands:

- `make venv`: Create a virtual environment and install dependencies.
- `make test`: Run unit tests using `pytest`.
- `make lint`: Run `ruff` and `ansible-lint` to check code quality.
- `make format`: Auto-format code using `ruff`.
- `make build`: Build the Ansible collection tarball (`.tar.gz`) for release.
- `make publish`: Build and publish the collection to Ansible Galaxy.

**Publishing a new release:**
To publish a release, you must provide your Ansible Galaxy API key:
```bash
make publish GALAXY_API_KEY="your_api_key_here" [VERSION=0.0.4]
```

## License

[MIT](LICENSE.md)
