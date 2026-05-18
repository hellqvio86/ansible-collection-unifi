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
# optional: export UNIFI_VALIDATE_CERTS="false"
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

## 4. Troubleshooting

If a module fails, it will return an `info` object containing the raw API response and status code from the UniFi controller. This is essential for debugging authorization or validation errors.
