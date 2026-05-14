# hellqvio86.unifi.unifi_info

Gather information about UniFi infrastructure.

## Description
The `unifi_info` module is the "Read-Only" engine of the collection. It allows you to gather the current state of your controller to audit or bootstrap your IaC.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `gather_subset` | list | No | `['wifi', 'firewall_groups', 'firewall_zones', 'firewall_policies', 'rsyslog']` | Which subsets of data to gather. |

## Examples

### 1. Gather Everything (Full Audit)
```yaml
- name: Gather all UniFi state
  hellqvio86.unifi.unifi_info:
    gather_subset:
      - wifi
      - firewall_groups
      - firewall_zones
      - firewall_policies
      - rsyslog
      - port_profiles
  register: unifi_state
```

### 2. Targeted: WiFi Networks Only
```yaml
- name: Gather WiFi details
  hellqvio86.unifi.unifi_info:
    gather_subset: ["wifi"]
  register: wifi_state

- name: Debug WiFi names
  debug:
    msg: "Found SSIDs: {{ wifi_state.unifi_info.wifi | map(attribute='name') | list }}"
```

### 3. Targeted: Firewall Groups & Policies
```yaml
- name: Gather Firewall state
  hellqvio86.unifi.unifi_info:
    gather_subset:
      - firewall_groups
      - firewall_policies
  register: fw_state
```

### 4. Targeted: System Settings (Syslog)
```yaml
- name: Check Syslog configuration
  hellqvio86.unifi.unifi_info:
    gather_subset: ["rsyslog"]
  register: syslog_state
```

## Return Values
The module returns a dictionary `unifi_info` containing keys for each requested subset.

| Key | Type | Description |
|-----|------|-------------|
| `wifi` | list | List of wireless network configurations. |
| `firewall_groups` | list | List of IP and Port groups. |
| `firewall_zones` | list | List of network zones. |
| `firewall_policies` | list | List of Policy Engine rules. |
| `rsyslog` | dict | Current remote syslog configuration. |
| `port_profiles` | list | List of switch port profiles. |
| `devices` | list | Raw data for all managed devices. |
