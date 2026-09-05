#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_port_profile
short_description: Manage UniFi switch port profiles
version_added: "0.0.1"
description:
    - Create, update, or delete port profiles in a UniFi controller.
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
        default: true
        type: bool
    api_key:
        description:
            - Token for direct API authentication (UniFi OS 3.x+ / Network 8.x+).
            - Preferred over username/password.
            - Can also be set via the C(UNIFI_API_KEY) or C(UNIFI_API_TOKEN) environment variables.
        type: str
        required: false
    ca_path:
        description: Path to CA bundle file for TLS verification.
        required: false
        type: path
    state:
        description: Whether the profile should be present or absent.
        choices: [ present, absent ]
        default: present
        type: str
    name:
        description: Name of the port profile.
        required: false
        type: str
    native_network_name:
        description: Name of the native (untagged) network.
        type: str
    tagged_network_names:
        description: List of names of tagged networks.
        type: list
        elements: str
    autoneg:
        description: Whether to enable auto-negotiation.
        type: bool
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI, find_resource, make_diff


def run_module():
    module_args = dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        id=dict(type="str", required=False),
        native_network_name=dict(type="str"),
        tagged_network_names=dict(type="list", elements="str"),
        autoneg=dict(type="bool"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    api = UnifiAPI(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"],
        module.params["validate_certs"],
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
        ca_path=module.params.get("ca_path"),
        api_key=module.params.get("api_key"),
    )
    api.login()

    site = module.params["site"]

    # Fetch existing port profiles
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    profiles = api.as_list(res)
    if res is None:
        module.fail_json(msg="Failed to fetch port profiles", info=info)

    existing = find_resource(
        module, profiles, "port profile", name=module.params["name"], resource_id=module.params.get("id")
    )

    # Fetch networks once for resolution
    networks_res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    networks = api.as_list(networks_res)
    network_map = {}
    for n in networks:
        if isinstance(n, dict) and "name" in n:
            if n["name"] in network_map:
                module.fail_json(msg=f"Ambiguous resource: multiple networks found with name '{n['name']}'")
            network_map[n["name"]] = n["_id"]

    # Build payload
    desired_payload = {"name": module.params["name"]}

    # Track LAN network IDs for exclusion calculation
    lan_network_ids = [n["_id"] for n in networks if isinstance(n, dict) and n.get("purpose") != "wan" and "_id" in n]

    nn_id = None
    if module.params["native_network_name"]:
        nn_id = network_map.get(module.params["native_network_name"])
        if not nn_id:
            module.fail_json(msg=f"Native network '{module.params['native_network_name']}' not found")
        desired_payload["native_networkconf_id"] = nn_id

    if module.params["tagged_network_names"] is not None:
        tn_ids = []
        for name in module.params["tagged_network_names"]:
            tn_id = network_map.get(name)
            if not tn_id:
                module.fail_json(msg=f"Tagged network '{name}' not found")
            tn_ids.append(tn_id)

        # In modern UniFi controller API, tagged networks are represented by tagged_vlan_mgmt="custom",
        # forward="customize", and excluded_networkconf_ids containing all LAN networks EXCEPT native and tagged.
        desired_payload["tagged_vlan_mgmt"] = "custom"
        desired_payload["forward"] = "customize"
        desired_payload["excluded_networkconf_ids"] = [
            nid for nid in lan_network_ids if nid != nn_id and nid not in tn_ids
        ]

    if module.params["autoneg"] is not None:
        desired_payload["autoneg"] = module.params["autoneg"]

    changed = False
    result_profile = existing

    if module.params["state"] == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                res, info = api.request(
                    f"/proxy/network/api/s/{site}/rest/portconf", method="POST", data=desired_payload
                )
                res_list = api.as_list(res)
                result_profile = res_list[0] if res_list else res
                if not result_profile:
                    module.fail_json(msg="Failed to create port profile", info=info)
            else:
                result_profile = desired_payload
        else:
            for key, value in desired_payload.items():
                if key == "excluded_networkconf_ids":
                    existing_list = existing.get(key) or []
                    if sorted(existing_list) != sorted(value):
                        changed = True
                        break
                elif existing.get(key) != value:
                    changed = True
                    break

            if changed:
                if not module.check_mode:
                    res, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="PUT", data=desired_payload
                    )
                    res_list = api.as_list(res)
                    result_profile = res_list[0] if res_list else res
                    if not result_profile:
                        module.fail_json(msg="Failed to update port profile", info=info)
                else:
                    result_profile = {**existing, **desired_payload}

    elif module.params["state"] == "absent":
        if existing:
            changed = True
            if not module.check_mode:
                _, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="DELETE")
                if info["status"] not in [200, 204]:
                    module.fail_json(msg="Failed to delete port profile", info=info)
            result_profile = None

    exit_kwargs = {"changed": changed, "profile": result_profile}
    if getattr(module, "_diff", False) is True:
        before = existing if existing else {}
        after = result_profile if result_profile else {}
        exit_kwargs["diff"] = make_diff(before, after)


    module.exit_json(**exit_kwargs)



if __name__ == "__main__":
    run_module()
