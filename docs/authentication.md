# Authentication Guide

The UniFi collection supports multiple ways to provide credentials to the controller API. All modules require a `host`, `username`, and `password`.

## 1. Module Parameters (Direct)

The most direct way is to provide credentials to each task. This is useful for one-off tasks but can lead to cluttered playbooks.

```yaml
- name: Manage WiFi
  hellqvio86.unifi.unifi_wlan:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    name: "MySSID"
```

## 2. Module Defaults (Recommended)

To avoid repetition, you can define credentials once at the play or block level using `module_defaults`. This automatically applies the parameters to all modules in the collection.

```yaml
- name: Manage UniFi Infrastructure
  hosts: localhost
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      username: "admin"
      password: "password"
  tasks:
    - name: Task 1 (No credentials needed)
      hellqvio86.unifi.unifi_wlan:
        name: "MySSID"
```

## 3. Environment Variables

Modules will fallback to environment variables if parameters are not provided in the task or defaults. This is ideal for CI/CD pipelines or local development.

| Variable | Parameter | Default |
|----------|-----------|---------|
| `UNIFI_HOST` | `host` | |
| `UNIFI_USERNAME` | `username` | |
| `UNIFI_PASSWORD` | `password` | |
| `UNIFI_VALIDATE_CERTS` | `validate_certs` | `false` |

## SSL Certificate Validation

By default, modules do not verify SSL certificates (ideal for self-signed certificates on local controllers). To enable verification:
* Set `validate_certs: true` in the task.
* Set `UNIFI_VALIDATE_CERTS=true` in your environment.
