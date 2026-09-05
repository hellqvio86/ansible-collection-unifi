# UniFi API & Controller Compatibility Matrix

This document defines the supported versions, endpoint families, and compatibility guarantees for the `hellqvio86.unifi` Ansible collection.

---

## 1. Supported Controller Matrix

| Controller Software | Supported Versions | Tested Versions | Supported Features / Modules | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **UniFi Network** | **8.0.0+** | 8.0.28, 8.1.113, 8.2.93 | **All Network Modules**:<br>• Policy Engine v2 (`unifi_firewall_policy`, `unifi_firewall_zone`, `unifi_nat_rule`)<br>• REST Configuration (`unifi_wlan`, `unifi_port_profile`, `unifi_switch_profile`, `unifi_firewall_group`, `unifi_dhcp_*`, `unifi_rsyslog`, `unifi_system_settings`) | **Recommended**. Standard on modern UniFi Gateway firmware. |
| **UniFi Network** | **7.0.0 - 7.5.x** | 7.4.156, 7.5.176 | **REST Configuration Only**:<br>• `unifi_wlan`<br>• `unifi_port_profile`<br>• `unifi_switch_profile`<br>• `unifi_firewall_group`<br>• `unifi_dhcp_*`<br>• `unifi_rsyslog` | **Partial Support**. Policy Engine v2 modules will fail with a clear incompatibility error. |
| **UniFi OS** | **3.0.0+** | 3.1.16, 3.2.12, 4.0.6 | **All Host Modules & Auth**:<br>• API Token authentication (`api_key`)<br>• User certificates (`unifi_user_certificate`)<br>• Persistent SSH keys (`unifi_ssh_key`)<br>• SSL certificate installation (`unifi_ssl_config`) | Standard on UniFi Dream Machines (UDM, UDM-Pro, UDM-SE), UXG, and Cloud Gateways. |
| **UniFi OS** | **< 3.0.0** | 1.12.x, 2.5.x | **Legacy Auth Only**:<br>• Username/password session authentication (`/api/auth/login`)<br>• REST Network modules | API Token authentication and `unifi_user_certificate` are not supported. |

---

## 2. API Generation & Endpoint Families

The collection interfaces with three distinct API families across Ubiquiti controllers. Each family is purpose-built and managed cleanly through centralized routing (`UnifiEndpoints`).

```text
                                  ┌────────────────────────────────────────┐
                                  │      UniFi Controller Platform         │
                                  └───────────────────┬────────────────────┘
                                                      │
              ┌───────────────────────────────────────┼────────────────────────────────────────┐
              ▼                                       ▼                                        ▼
   ┌──────────────────────┐               ┌──────────────────────┐                ┌──────────────────────┐
   │   Legacy REST API    │               │   Policy Engine v2   │                │     UniFi OS Core    │
   │  (/proxy/network/    │               │  (/proxy/network/v2/ │                │        (/api/)       │
   │   api/s/<site>/...)  │               │   api/site/<site>/)  │                │                      │
   └──────────┬───────────┘               └──────────┬───────────┘                └──────────┬───────────┘
              │                                      │                                       │
              ▼                                      ▼                                       ▼
    • unifi_wlan                           • unifi_firewall_policy                 • API key / session login
    • unifi_port_profile                   • unifi_firewall_zone                   • unifi_user_certificate
    • unifi_switch_profile                 • unifi_nat_rule                        • unifi_ssh_key
    • unifi_firewall_group                                                         • unifi_ssl_config
    • unifi_dhcp_server
    • unifi_dhcp_reservation
    • unifi_rsyslog
```

### 1. Legacy REST API (`/proxy/network/api/s/{site}/rest/...`)
- **Applicability**: UniFi Network 7.x - 9.x.
- **Purpose**: Stable endpoints representing network infrastructure objects such as Wireless LAN configurations (`wlanconf`), switch port configuration profiles (`portconf`), IP networks (`networkconf`), and IP/Port firewall groups (`firewallgroup`).
- **Design Rationale**: These endpoints remain the official, battle-tested interface for core switching, wireless, and network layer configuration.

### 2. Policy Engine v2 API (`/proxy/network/v2/api/site/{site}/...`)
- **Applicability**: UniFi Network 8.0+.
- **Purpose**: Modern zone-based firewalling, stateful traffic rules, and policy routing.
- **Design Rationale**: Ubiquiti overhauled firewall rule processing in UniFi Network 8.0, replacing legacy iptables indices with zone-based policy routing (`firewall-zone` and `firewall-rule`). Modules target v2 directly to support modern multi-WAN, traffic flow policies, and inter-VLAN zone isolation.

### 3. UniFi OS Core API (`/api/...`)
- **Applicability**: UniFi OS 3.x+.
- **Purpose**: System-level administrative management on UniFi OS console appliances.
- **Design Rationale**: Handles administrator authentication (`/api/auth/login`), API token authorization (`X-API-KEY`), and user/client certificate lifecycle management (`/api/userCertificates`).

---

## 3. Incompatibility Protection

The collection implements strict capability verification through `UnifiCompatibility`. When an unsupported controller version is detected for a feature, modules fail with actionable diagnostics rather than vague HTTP 404 or JSON parsing errors:

```text
UniFi Network version '7.5.176' does not support the Policy Engine (v2 API). Minimum required version is 8.0.0.
```
