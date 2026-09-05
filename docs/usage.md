# Usage Best Practices

Managing UniFi as Code requires a few best practices to ensure stability and idempotency.

## 1. Using the Policy Engine (v2 API)

For modern UniFi devices (UDM, UXG), use the `unifi_firewall_policy` and `unifi_firewall_zone` modules. These target the modern v2 API (Policy Engine) rather than the legacy REST-based firewall rules.

## 2. Information Gathering

The `unifi_info` module is your best tool for auditing your current state. You can gather specific subsets of data to keep your playbooks fast.

For full onboarding exports, run the bundled playbook:

```bash
export UNIFI_HOST="192.0.2.1"
export UNIFI_USERNAME="admin"
export UNIFI_PASSWORD="password"
# optional: export UNIFI_SITE="default"
# optional: export UNIFI_VALIDATE_CERTS="false" # defaults to "true" for security
# optional: export UNIFI_CA_PATH="/path/to/ca.pem"
# optional: export UNIFI_DUMP_DIR="./unifi_dump"

ansible-playbook playbooks/unifi_dump_all.yml
```

```yaml
- name: Gather WiFi and Firewall state
  hellqvio86.unifi.unifi_info:
    gather_subset:
      - wifi
      - firewall_groups
  register: info
```

## 3. Idempotency

All modules in this collection are designed to be idempotent. They will fetch the current state from the controller and only perform a `POST`, `PUT`, or `DELETE` if the desired state differs from the actual state.

## 4. Check Mode Guarantees

All configuration modules support Ansible check mode (`--check`).

- **Zero Mutations**: The underlying API client strictly enforces read-only behavior during check mode. Any mutating HTTP request (`POST`, `PUT`, `PATCH`, `DELETE` outside authentication) is immediately intercepted and blocked.
- **Remote Read Requirement**: Check mode performs remote read operations (`GET`) to inspect actual controller state. Valid credentials and network reachability to the UniFi controller are required.
- **Accurate Change Prediction**: Modules accurately predict `changed: true` or `false` and construct the anticipated post-change resource representation without applying modifications on the controller.

## 5. Diff Mode & Secret Sanitization

Resource modules support Ansible diff mode (`--diff`).

- When run with `--diff`, modules return structured `before` and `after` representations showing the specific attributes that will change.
- **Secret Masking**: All sensitive parameters—including Wi-Fi passphrases (`passphrase`, `x_passphrase`), user passwords, API tokens, session cookies, and private key material (`private_key`, `private_key_content`)—are automatically masked with `"********"` to prevent credential leakage in console output, play logs, and CI/CD runs.

## 6. Rate Limiting, Locking, and Timeouts

- **Cross-Process Host Locking**: To protect the UniFi controller from concurrent request overload, dropped connections, and daemon instability (especially on Cloud Keys and Dream Machines), API requests coordinate through a per-host lock file (`/tmp/ansible_unifi_{host_hash}.lock`). Hosts are hashed individually so operations targeting distinct controllers run in parallel without contention.
- **Lock Acquisition Timeout**: Lock acquisition times out after 30 seconds if an orphaned lock was abandoned by an interrupted process, ensuring playbooks never freeze indefinitely.
- **Inter-Request Rate Limiting**: Consecutive requests to the same controller enforce a minimum delay (50ms) to maintain a healthy request cadence.
- **Safe Retries & Non-Idempotent Protection**: Transient gateway errors (502, 503, 504) and rate limits (429) trigger exponential backoff with jitter and honor controller `Retry-After` headers. To prevent duplicate resource creation, mutating `POST` requests are never retried on 5xx errors.
- **Configurable Timeout**: Request timeout defaults to 30 seconds and can be customized via the `timeout` parameter or the `UNIFI_TIMEOUT` environment variable.

## 7. Troubleshooting

If a module fails, it will return an `info` object containing the sanitized error message and status code from the UniFi controller. This is essential for debugging authorization, network, or validation errors without exposing sensitive session headers.
