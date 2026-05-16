#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_dhcp_reservation
short_description: Manage DHCP fixed IP reservations on a UniFi controller
version_added: "0.0.6"
description:
    - Create, update, or delete DHCP fixed IP (static) reservations for known client devices on a UniFi controller.
    - The client device must already be known to the controller (have connected at least once).
    - Uses the C(/proxy/network/api/s/{site}/stat/alluser) endpoint to discover known clients and
      C(/proxy/network/api/s/{site}/rest/user/{_id}) to apply changes.
options:
    host:
        description: The host of the UniFi controller.
        required: false
        type: str
    username:
        description: UniFi controller username.
        required: false
        type: str
    password:
        description: UniFi controller password.
        required: false
        type: str
    site:
        description: UniFi site name.
        default: default
        type: str
    validate_certs:
        description: Verify SSL certificates.
        default: false
        type: bool
    state:
        description:
            - Whether the DHCP reservation should be present or absent.
            - C(present) ensures the client has a fixed IP reservation.
            - C(absent) removes the fixed IP reservation from the client.
        choices: [ present, absent ]
        default: present
        type: str
    mac:
        description:
            - MAC address of the client device.
            - The client must already be known to the UniFi controller.
        required: true
        type: str
    name:
        description:
            - Friendly name to assign to the client device.
            - If not provided, the existing name is kept.
        required: false
        type: str
    fixed_ip:
        description:
            - Static IP address to assign to the client.
            - Required when C(state=present).
        required: false
        type: str
    network_name:
        description:
            - Name of the network (LAN) for the fixed IP reservation.
            - If not provided, the existing network assignment is kept.
        required: false
        type: str
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Ensure a DHCP reservation exists
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:01"
    name: "Example Device"
    fixed_ip: "198.51.100.71"
    network_name: "Default"

- name: Remove a DHCP reservation
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:02"
    state: absent
"""

RETURN = r"""
changed:
    description: Whether any change was applied.
    type: bool
    returned: always
reservation:
    description: The current state of the reservation after the operation.
    type: dict
    returned: when state is present and client is found
    sample: {"_id": "...", "mac": "02:1a:2b:3c:4d:01", "fixed_ip": "198.51.100.71", "use_fixedip": true}
client:
    description: The current state of the client after the operation.
    type: dict
    returned: when client is found
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        mac=dict(type="str", required=True),
        name=dict(type="str", required=False),
        fixed_ip=dict(type="str", required=False),
        network_name=dict(type="str", required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Validate fixed_ip is provided when state=present
    if module.params["state"] == "present" and not module.params["fixed_ip"]:
        module.fail_json(msg="'fixed_ip' is required when state=present")

    api = UnifiAPI(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"],
        module.params["validate_certs"],
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
    )
    api.login()

    site = module.params["site"]
    mac = module.params["mac"].lower()
    state = module.params["state"]

    # Fetch all known clients
    res, info = api.request(f"/proxy/network/api/s/{site}/stat/alluser")
    all_clients = api.as_list(res)
    if info["status"] != 200:
        module.fail_json(msg="Failed to fetch known clients", info=info)

    client = next(
        (c for c in all_clients if isinstance(c, dict) and c.get("mac", "").lower() == mac),
        None,
    )
    if not client:
        module.fail_json(
            msg=f"Client with MAC '{mac}' not found among known devices. "
            "The device must have connected to the UniFi controller at least once."
        )

    changed = False
    result_client = client

    # Resolve network_name to network_id if provided
    network_id = None
    if module.params["network_name"]:
        networks_res, _ = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
        networks = api.as_list(networks_res)
        network = next(
            (n for n in networks if isinstance(n, dict) and n.get("name") == module.params["network_name"]),
            None,
        )
        if not network:
            module.fail_json(msg=f"Network '{module.params['network_name']}' not found")
        network_id = network["_id"]

    if state == "present":
        desired_payload = {"use_fixedip": True}

        if module.params["fixed_ip"]:
            desired_payload["fixed_ip"] = module.params["fixed_ip"]
        if network_id:
            desired_payload["network_id"] = network_id
        if module.params["name"]:
            desired_payload["name"] = module.params["name"]

        needs_update = False

        if not client.get("use_fixedip"):
            needs_update = True
        elif client.get("fixed_ip") != module.params["fixed_ip"]:
            needs_update = True
        elif network_id and client.get("network_id") != network_id:
            needs_update = True
        elif module.params["name"] and client.get("name") != module.params["name"]:
            needs_update = True

        if needs_update:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/user/{client['_id']}",
                    method="PUT",
                    data=desired_payload,
                )
                if info["status"] not in [200, 201]:
                    module.fail_json(msg="Failed to update DHCP reservation", info=info)
                res_list = api.as_list(res)
                result_client = res_list[0] if res_list else res

        module.exit_json(
            changed=changed,
            reservation={
                "mac": result_client.get("mac"),
                "name": result_client.get("name"),
                "fixed_ip": result_client.get("fixed_ip"),
                "use_fixedip": result_client.get("use_fixedip"),
                "network_id": result_client.get("network_id"),
            },
            client=result_client,
        )

    elif state == "absent":
        if client.get("use_fixedip"):
            changed = True
            if not module.check_mode:
                payload = {"use_fixedip": False}
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/user/{client['_id']}",
                    method="PUT",
                    data=payload,
                )
                if info["status"] not in [200, 201]:
                    module.fail_json(msg="Failed to remove DHCP reservation", info=info)
                res_list = api.as_list(res)
                result_client = res_list[0] if res_list else res

        module.exit_json(changed=changed, client=result_client)


if __name__ == "__main__":
    run_module()
