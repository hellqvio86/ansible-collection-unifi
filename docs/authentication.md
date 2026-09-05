# Authentication Guide

The UniFi collection supports multiple authentication methods for connecting to UniFi OS and UniFi Network.

## 1. API Token Authentication (Preferred & Recommended)

For UniFi OS 3.x+ / UniFi Network 8.x+, **API Token authentication** is the preferred and most secure method. It uses the `X-API-KEY` header directly, eliminating the need to store or transmit long-lived administrator passwords in playbooks, and skips session login handshakes.

### Generating an API Token
In the UniFi OS web interface:
1. Go to **OS Settings** > **Admins & Users** (or **System** > **Administration**).
2. Select an admin account or create an automation account.
3. Click **API Token** and generate a new key.

### Using an API Token in Playbooks
Pass `api_key` directly or via `module_defaults`:

```yaml
- name: Manage UniFi Infrastructure
  hosts: localhost
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.0.2.1"
      api_key: "{{ vault_unifi_api_key }}"
  tasks:
    - name: Ensure Home WiFi is present
      hellqvio86.unifi.unifi_wlan:
        name: "HomeWiFi"
        passphrase: "securepassword"
        state: present
```

### Using an API Token via Environment Variables
In CI/CD pipelines or local automation, export `UNIFI_API_KEY`:

```bash
export UNIFI_HOST="192.0.2.1"
export UNIFI_API_KEY="your-unifi-api-token-here"
ansible-playbook site.yml
```

---

## 2. Session Cookie & CSRF Token Reuse

For environments where you authenticate once externally or via an authentication step, you can pass pre-authenticated session credentials directly:

```yaml
- name: Manage WiFi with existing session
  hellqvio86.unifi.unifi_wlan:
    host: "192.0.2.1"
    unifi_session_cookie: "TOKEN=...; SESSION=..."
    unifi_csrf_token: "csrf-token-value"
    name: "MySSID"
```

---

## 3. Username & Password (Legacy Fallback)

If running older UniFi controller versions that do not support API tokens, you can provide an administrator `username` and `password`. The collection logs in via `/api/auth/login` to obtain an ephemeral session:

```yaml
- name: Manage WiFi with username/password
  hellqvio86.unifi.unifi_wlan:
    host: "192.0.2.1"
    username: "admin"
    password: "{{ vault_admin_password }}"
    name: "MySSID"
```

---

## 4. Environment Variables Reference

Modules automatically fall back to environment variables when parameters are not provided in task or module defaults:

| Variable | Parameter | Description |
|----------|-----------|-------------|
| `UNIFI_HOST` | `host` | Controller hostname or IP |
| `UNIFI_API_KEY` / `UNIFI_API_TOKEN` | `api_key` | **(Preferred)** API token for UniFi OS 3.x+ |
| `UNIFI_USERNAME` | `username` | Administrator username |
| `UNIFI_PASSWORD` | `password` | Administrator password |
| `UNIFI_VALIDATE_CERTS` | `validate_certs` | Validate TLS certificates (default: `true`) |
| `UNIFI_CA_PATH` | `ca_path` | Custom CA bundle path |

---

## SSL / TLS Certificate Validation

By default, all modules verify SSL/TLS certificates for security.

* **Custom CA bundles**: If your UniFi controller uses a certificate signed by an internal or private CA, supply the CA bundle via `ca_path` in the task or set `UNIFI_CA_PATH=/path/to/ca.pem` in your environment.
* **Disabling verification (insecure)**: For test/lab controllers using self-signed certificates where CA trust cannot be configured, you can explicitly disable verification by setting `validate_certs: false` on the task or `UNIFI_VALIDATE_CERTS=false` in the environment. When certificate validation is disabled, a warning is emitted. Disabling TLS verification in production is strongly discouraged.


