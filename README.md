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

- `hellqvio86.unifi.unifi_firewall_policy`: Manage modern firewall rules.
- `hellqvio86.unifi.unifi_ssh_key`: Manage system-level SSH keys.
- `hellqvio86.unifi.unifi_ssl_config`: Deploy SSL certificates via modulated SSH transport.

## Requirements

- Python >= 3.10
- `PyJWT` (for token handling)
- `paramiko` (for SSH-modulated tasks)

## Installation

```bash
ansible-galaxy collection install hellqvio86.unifi
```

## Example Usage

### Managing Firewall Rules

```yaml
- name: Allow DNS to Local Server
  hellqvio86.unifi.unifi_firewall_policy:
    host: "{{ unifi_ip }}"
    username: "{{ unifi_user }}"
    password: "{{ unifi_password }}"
    name: "Allow DNS"
    action: "ALLOW"
    protocol: "tcp_udp"
    destination:
      ips: ["192.168.1.10"]
      port: "53"
```

### Managing SSH Keys

```yaml
- name: Ensure admin keys are present
  hellqvio86.unifi.unifi_ssh_key:
    host: "{{ unifi_ip }}"
    username: "{{ unifi_user }}"
    password: "{{ unifi_password }}"
    keys:
      - "ssh-rsa AAAAB3Nza..."
```

## License

[MIT](LICENSE.md)
