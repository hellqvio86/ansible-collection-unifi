#!/usr/bin/python


DOCUMENTATION = r'''
---
module: unifi_firewall_policy
short_description: Manage UniFi v8.3+ Policy Engine Firewall Rules
version_added: "0.0.1"
description:
    - Create, update, or delete firewall policies in a UniFi controller using the modern Policy Engine (Zone-Based Firewall).
    - This module targets the v2 API introduced in UniFi Network 8.x.
options:
    host:
        description: The host of the UniFi controller (e.g., 192.168.1.1).
        required: true
        type: str
    username:
        description: UniFi controller username.
        required: true
        type: str
    password:
        description: UniFi controller password.
        required: true
        type: str
    site:
        description: UniFi site name (typically 'default').
        default: default
        type: str
    validate_certs:
        description: Verify SSL certificates.
        default: false
        type: bool
    state:
        description: Whether the policy should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the firewall policy.
        required: true
        type: str
    action:
        description: Action to take.
        choices: [ ALLOW, BLOCK, REJECT, ISOLATE ]
        default: ALLOW
        type: str
    protocol:
        description: Protocol to match.
        choices: [ all, tcp, udp, tcp_udp, icmp, icmpv6 ]
        default: all
        type: str
    index:
        description: Rule index (order).
        type: int
        default: 10000
    enabled:
        description: Whether the rule is enabled.
        type: bool
        default: true
    logging:
        description: Whether to log matches.
        type: bool
        default: false
    source:
        description: Source configuration.
        type: dict
        suboptions:
            zone:
                description: Source zone name (e.g., Internal, External, Guest).
                type: str
                default: Internal
            matching_target:
                description: Type of source to match.
                choices: [ ANY, IP, NETWORK, DOMAIN ]
                default: ANY
                type: str
            ips:
                description: List of IP addresses or subnets.
                type: list
                elements: str
            port:
                description: Port or port range.
                type: str
    destination:
        description: Destination configuration.
        type: dict
        suboptions:
            zone:
                description: Destination zone name.
                type: str
                default: Internal
            matching_target:
                description: Type of destination to match.
                choices: [ ANY, IP, NETWORK, DOMAIN ]
                default: ANY
                type: str
            ips:
                description: List of IP addresses or subnets.
                type: list
                elements: str
            port:
                description: Port or port range.
                type: str
author:
    - hellqvio86 (@hellqvio86)
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True, no_log=True),
        password=dict(type='str', required=True, no_log=True),
        site=dict(type='str', default='default'),
        validate_certs=dict(type='bool', default=False),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        name=dict(type='str', required=True),
        action=dict(type='str', choices=['ALLOW', 'BLOCK', 'REJECT', 'ISOLATE'], default='ALLOW'),
        protocol=dict(type='str', choices=['all', 'tcp', 'udp', 'tcp_udp', 'icmp', 'icmpv6'], default='all'),
        index=dict(type='int', default=10000),
        enabled=dict(type='bool', default=True),
        logging=dict(type='bool', default=False),
        source=dict(type='dict', default={}),
        destination=dict(type='dict', default={})
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    site = module.params['site']
    validate_certs = module.params['validate_certs']
    state = module.params['state']
    
    # 1. Initialize API and Login
    api = UnifiAPI(module, host, username, password, validate_certs)
    api.login()

    # 2. Defaults for nested dicts
    src_params = {'zone': 'Internal', 'matching_target': 'ANY', 'ips': [], 'port': ''}
    src_params.update(module.params['source'])
    
    dst_params = {'zone': 'Internal', 'matching_target': 'ANY', 'ips': [], 'port': ''}
    dst_params.update(module.params['destination'])

    # 3. Resolve Zones
    zones, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall/zone")
    if not zones:
        module.fail_json(msg="Failed to fetch zones", info=info)
        
    zone_map = {z['name']: z['_id'] for z in zones}
    src_zone_id = zone_map.get(src_params['zone'])
    dst_zone_id = zone_map.get(dst_params['zone'])
    
    if not src_zone_id or not dst_zone_id:
        module.fail_json(msg="Zone not found", src_zone=src_params['zone'], dst_zone=dst_params['zone'], available_zones=list(zone_map.keys()))

    # 4. Get existing policies
    policies, info = api.request(f"/proxy/network/v2/api/site/{site}/firewall-policies")
    if policies is None:
        module.fail_json(msg="Failed to fetch policies", info=info)
    
    existing = None
    for p in policies:
        if p.get('name') == module.params['name'] and \
           p.get('source', {}).get('zone_id') == src_zone_id and \
           p.get('destination', {}).get('zone_id') == dst_zone_id:
            existing = p
            break

    # Build the payload for the current desired state
    desired_payload = {
        "name": module.params['name'],
        "action": module.params['action'],
        "protocol": module.params['protocol'],
        "index": module.params['index'],
        "enabled": module.params['enabled'],
        "logging": module.params['logging'],
        "ip_version": "BOTH",
        "schedule": {"mode": "ALWAYS"},
        "source": {
            "zone_id": src_zone_id,
            "matching_target": src_params['matching_target'],
            "ips": src_params['ips'],
            "matching_target_type": "SPECIFIC",
            "port_matching_type": "SPECIFIC" if src_params['port'] else "ANY"
        },
        "destination": {
            "zone_id": dst_zone_id,
            "matching_target": dst_params['matching_target'],
            "ips": dst_params['ips'],
            "matching_target_type": "SPECIFIC",
            "port_matching_type": "SPECIFIC" if dst_params['port'] else "ANY"
        }
    }
    
    if src_params['port']:
        desired_payload['source']['port'] = src_params['port']
    if dst_params['port']:
        desired_payload['destination']['port'] = dst_params['port']

    changed = False
    result_policy = existing

    if state == 'present':
        if not existing:
            changed = True
            if not module.check_mode:
                path = f"/proxy/network/v2/api/site/{site}/firewall-policies"
                result_policy, info = api.request(path, method='POST', data=desired_payload)
                if not result_policy:
                    module.fail_json(msg="Failed to create policy", info=info)
        else:
            # Check for differences
            for key in ['action', 'protocol', 'index', 'enabled', 'logging']:
                if existing.get(key) != desired_payload[key]:
                    changed = True
            
            if existing['source'].get('ips') != desired_payload['source']['ips'] or \
               existing['source'].get('port', '') != desired_payload['source'].get('port', '') or \
               existing['destination'].get('ips') != desired_payload['destination']['ips'] or \
               existing['destination'].get('port', '') != desired_payload['destination'].get('port', ''):
                changed = True

            if changed and not module.check_mode:
                path = f"/proxy/network/v2/api/site/{site}/firewall-policies/{existing['_id']}"
                result_policy, info = api.request(path, method='PUT', data=desired_payload)
                if not result_policy:
                    module.fail_json(msg="Failed to update policy", info=info)

    elif state == 'absent':
        if existing:
            changed = True
            if not module.check_mode:
                path = f"/proxy/network/v2/api/site/{site}/firewall-policies/{existing['_id']}"
                _, info = api.request(path, method='DELETE')
                if info['status'] not in [200, 204]:
                    module.fail_json(msg="Failed to delete policy", info=info)
            result_policy = None

    module.exit_json(changed=changed, policy=result_policy)

if __name__ == '__main__':
    run_module()
