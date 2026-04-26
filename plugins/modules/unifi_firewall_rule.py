#!/usr/bin/python


DOCUMENTATION = r'''
---
module: unifi_firewall_rule
short_description: Manage UniFi firewall rules
version_added: "0.0.1"
description:
    - Create, update, or delete firewall rules in a UniFi controller.
options:
    host:
        description:
            - The base URL of the UniFi controller (e.g., https://192.168.1.1).
        required: true
        type: str
    username:
        description:
            - UniFi controller username.
        required: true
        type: str
    password:
        description:
            - UniFi controller password.
        required: true
        type: str
    site:
        description:
            - UniFi site name (typically 'default').
        default: default
        type: str
    validate_certs:
        description:
            - Verify SSL certificates.
        default: false
        type: bool
    name:
        description:
            - Name of the firewall rule.
        required: true
        type: str
    ruleset:
        description:
            - The ruleset to apply this to (e.g., LAN_IN, GUEST_IN).
        required: true
        type: str
    state:
        description:
            - Whether the rule should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
author:
    - hellqvio86 (@hellqvio86)
'''

EXAMPLES = r'''
- name: Block IoT to LAN
  hellqvio86.unifi.unifi_firewall_rule:
    host: "https://192.168.60.1"
    username: "admin"
    password: "password123"
    site: "default"
    validate_certs: false
    name: "Block IoT to LAN"
    ruleset: "LAN_IN"
    state: "present"
'''

RETURN = r'''
rule:
    description: The created or updated firewall rule object.
    type: dict
    returned: when state is present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def login(module, host, username, password, validate_certs):
    login_url = f"{host}/api/auth/login"
    data = json.dumps({"username": username, "password": password})
    headers = {"Content-Type": "application/json"}
    
    response, info = fetch_url(module, login_url, data=data, headers=headers, method='POST')
    
    if info['status'] != 200:
        module.fail_json(msg="Login failed", info=info)
    
    # Extract Cookies and CSRF token
    cookies = info.get('set-cookie', '')
    csrf_token = ''
    
    # Simple extraction (for Unifi OS 3.x+ usually the CSRF is in a specific header or cookie)
    # This might need refinement based on exact Unifi OS version
    for header_name, header_value in info.items():
        if header_name.lower() == 'x-csrf-token':
            csrf_token = header_value
            
    # For UniFi OS 3.x+, CSRF token might be returned in a cookie named TOKEN
    if not csrf_token:
        # Extract from cookie string if necessary
        cookie_parts = cookies.split(';')
        for part in cookie_parts:
            if 'TOKEN=' in part:
                csrf_token = part.split('TOKEN=')[1].strip()
                
    return cookies, csrf_token

def get_rules(module, host, site, cookies, csrf_token):
    url = f"{host}/proxy/network/api/s/{site}/rest/firewallrule"
    headers = {
        "Cookie": cookies,
        "X-CSRF-Token": csrf_token,
        "Content-Type": "application/json"
    }
    
    response, info = fetch_url(module, url, headers=headers, method='GET')
    
    if info['status'] != 200:
        module.fail_json(msg="Failed to fetch firewall rules", info=info)
        
    try:
        data = json.loads(response.read())
        return data.get('data', [])
    except Exception as e:
        module.fail_json(msg="Failed to parse JSON response", error=str(e))

def run_module():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True, no_log=True),
        password=dict(type='str', required=True, no_log=True),
        site=dict(type='str', default='default'),
        validate_certs=dict(type='bool', default=False),
        name=dict(type='str', required=True),
        ruleset=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    module.params['host']
    module.params['username']
    module.params['password']
    module.params['site']
    module.params['validate_certs']
    module.params['name']
    
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # 1. Login
    # cookies, csrf_token = login(module, host, username, password, validate_certs)
    
    # 2. Get existing rules
    # rules = get_rules(module, host, site, cookies, csrf_token)
    
    # 3. Check for existing rule by name
    # existing_rule = next((r for r in rules if r.get('name') == name), None)
    
    # (Simplified skeleton logic to show structure)
    if module.check_mode:
        module.exit_json(**result)

    result['message'] = "Module skeleton initialized"
    module.exit_json(**result)

if __name__ == '__main__':
    run_module()
