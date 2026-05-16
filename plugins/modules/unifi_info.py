#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_info
short_description: Gather information about UniFi infrastructure
version_added: "0.0.1"
description:
    - Gather details about WiFi networks, firewall groups, zones, policies, and settings from a UniFi controller.
options:
    host: {type: str}
    site: {type: str, default: default}
    validate_certs: {type: bool, default: false}
    gather_subset:
        description: List of subsets to gather.
        type: list
        elements: str
        choices: [ wifi, firewall_groups, firewall_zones, firewall_policies, rsyslog, port_profiles, devices, dhcp_reservations, networks ]
        default: [ wifi, firewall_groups, firewall_zones, firewall_policies, rsyslog ]
author:
    - hellqvio86 (@hellqvio86)
"""

import ipaddress

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        gather_subset=dict(
            type="list",
            elements="str",
            choices=["wifi", "firewall_groups", "firewall_zones", "firewall_policies", "rsyslog", "port_profiles", "devices", "dhcp_reservations", "networks"],
            default=["wifi", "firewall_groups", "firewall_zones", "firewall_policies", "rsyslog"],
        ),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    api = UnifiAPI(
        module,
        module.params.get("host"),
        module.params.get("username"),
        module.params.get("password"),
        module.params.get("validate_certs"),
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
    )
    api.login()

    site = module.params["site"]
    subset = module.params["gather_subset"]
    results = {}

    # Helper for mapping IDs to Names
    networks_res, _ = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    network_map = {n["_id"]: n["name"] for n in api.as_list(networks_res) if isinstance(n, dict)}

    # Build subnet -> name mapping for clients without network_id
    subnet_map = {}
    for n in api.as_list(networks_res):
        if isinstance(n, dict) and n.get("ip_subnet"):
            try:
                subnet_map[ipaddress.ip_network(n["ip_subnet"], strict=False)] = n["name"]
            except ValueError:
                pass

    if "wifi" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/rest/wlanconf")
        results["wifi"] = []
        for w in api.as_list(res):
            if not isinstance(w, dict):
                continue
            results["wifi"].append({
                "name": w.get("name"),
                "enabled": w.get("enabled"),
                "security": w.get("security"),
                "passphrase": w.get("x_passphrase"),
                "network": network_map.get(w.get("networkconf_id"), "Unknown"),
                "bands": w.get("wlan_bands")
            })

    if "firewall_groups" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/rest/firewallgroup")
        results["firewall_groups"] = []
        for g in api.as_list(res):
            if not isinstance(g, dict):
                continue
            results["firewall_groups"].append({
                "name": g.get("name"),
                "type": g.get("group_type"),
                "members": g.get("group_members")
            })

    if "firewall_zones" in subset:
        res, _ = api.request(f"/proxy/network/v2/api/site/{site}/firewall/zone")
        results["firewall_zones"] = []
        for z in api.as_list(res):
            if not isinstance(z, dict):
                continue
            results["firewall_zones"].append({
                "name": z.get("name"),
                "networks": [network_map.get(nid, nid) for nid in z.get("network_ids", [])]
            })

    if "firewall_policies" in subset:
        # Resolve zone IDs for mapping
        zones_res, _ = api.request(f"/proxy/network/v2/api/site/{site}/firewall/zone")
        zone_map = {z["_id"]: z["name"] for z in api.as_list(zones_res) if isinstance(z, dict)}

        res, _ = api.request(f"/proxy/network/v2/api/site/{site}/firewall-policies")
        results["firewall_policies"] = []
        for p in api.as_list(res):
            if not isinstance(p, dict):
                continue
            results["firewall_policies"].append({
                "name": p.get("name"),
                "action": p.get("action"),
                "protocol": p.get("protocol"),
                "index": p.get("index"),
                "enabled": p.get("enabled"),
                "source": {
                    "zone": zone_map.get(p.get("source", {}).get("zone_id")),
                    "ips": p.get("source", {}).get("ips", []),
                    "port": p.get("source", {}).get("port")
                },
                "destination": {
                    "zone": zone_map.get(p.get("destination", {}).get("zone_id")),
                    "ips": p.get("destination", {}).get("ips", []),
                    "port": p.get("destination", {}).get("port")
                }
            })

    if "rsyslog" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/get/setting")
        rsyslog = next((s for s in api.as_list(res) if isinstance(s, dict) and s.get("key") == "rsyslogd"), None)
        if rsyslog:
            results["rsyslog"] = {
                "enabled": rsyslog.get("enabled"),
                "ip": rsyslog.get("ip"),
                "port": rsyslog.get("port"),
                "log_all_contents": rsyslog.get("log_all_contents")
            }

    if "port_profiles" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
        results["port_profiles"] = []
        for p in api.as_list(res):
            if not isinstance(p, dict):
                continue
            results["port_profiles"].append({
                "name": p.get("name"),
                "native_network": network_map.get(p.get("native_networkconf_id")),
                "tagged_networks": [network_map.get(nid) for nid in p.get("tagged_networkconf_ids", [])]
            })

    if "devices" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/rest/device")
        results["devices"] = api.as_list(res)

    if "dhcp_reservations" in subset:
        res, _ = api.request(f"/proxy/network/api/s/{site}/stat/alluser")
        results["dhcp_reservations"] = []
        for c in api.as_list(res):
            if not isinstance(c, dict):
                continue
            if c.get("use_fixedip"):
                network_id = c.get("network_id")
                network = network_map.get(network_id, network_id) if network_id else None

                if not network:
                    fixed_ip = c.get("fixed_ip")
                    if fixed_ip:
                        try:
                            ip_addr = ipaddress.ip_address(fixed_ip)
                            for subnet, net_name in subnet_map.items():
                                if ip_addr in subnet:
                                    network = net_name
                                    break
                        except ValueError:
                            pass

                results["dhcp_reservations"].append({
                    "mac": c.get("mac"),
                    "name": c.get("name"),
                    "fixed_ip": c.get("fixed_ip"),
                    "network": network,
                })

    if "networks" in subset:
        results["networks"] = []
        for n in api.as_list(networks_res):
            if not isinstance(n, dict):
                continue
            results["networks"].append({
                "name": n.get("name"),
                "purpose": n.get("purpose"),
                "enabled": n.get("enabled"),
                "vlan_enabled": n.get("vlan_enabled"),
                "vlan": n.get("vlan"),
                "subnet": n.get("ip_subnet"),
                "dhcpd_enabled": n.get("dhcpd_enabled"),
                "dhcpd_start": n.get("dhcpd_start"),
                "dhcpd_stop": n.get("dhcpd_stop"),
                "dhcpd_leasetime": n.get("dhcpd_leasetime"),
                "dhcpd_dns_1": n.get("dhcpd_dns_1"),
                "dhcpd_dns_2": n.get("dhcpd_dns_2"),
                "dhcpd_gateway": n.get("dhcpd_gateway"),
                "dhcpd_domain_name": n.get("dhcpd_domain_name"),
            })

    module.exit_json(changed=False, unifi_info=results)


if __name__ == "__main__":
    run_module()
