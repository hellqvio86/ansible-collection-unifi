#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_port_profile
short_description: Manage UniFi Port Profiles (Port Configurations)
version_added: "0.0.1"
description:
    - Create, update, or delete port profiles in a UniFi controller.
    - Supports single profile mode and batch mode.
options:
    host:
        required: true
        type: str
    username:
        required: true
        type: str
    password:
        required: true
        type: str
    site:
        default: default
        type: str
    validate_certs:
        default: false
        type: bool
    state:
        choices: [ present, absent ]
        default: present
        type: str
    name:
        type: str
    native_network_name:
        type: str
    tagged_network_names:
        type: list
        elements: str
    poe_mode:
        choices: [ auto, off, passthrough ]
        type: str
    isolation:
        type: bool
    autoneg:
        default: true
        type: bool
    profiles:
        description:
            - Optional batch input. When provided, each item is processed with one shared UniFi login.
        type: list
        elements: dict
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def _as_data_list(payload):
    if payload is None:
        return []
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        return []
    if isinstance(payload, list):
        return payload
    return []


def _normalize_desired(module):
    batch = module.params.get("profiles") or []
    if batch:
        return batch
    if not module.params.get("name"):
        module.fail_json(msg="Either 'name' (single mode) or 'profiles' (batch mode) must be provided")
    return [
        {
            "state": module.params["state"],
            "name": module.params["name"],
            "native_network_name": module.params.get("native_network_name"),
            "tagged_network_names": module.params.get("tagged_network_names"),
            "poe_mode": module.params.get("poe_mode"),
            "isolation": module.params.get("isolation"),
            "autoneg": module.params.get("autoneg"),
        }
    ]


def _build_payload(module, item, network_map):
    desired_payload = {"name": item["name"], "autoneg": item.get("autoneg", True)}

    native_network_name = item.get("native_network_name")
    if native_network_name:
        native_id = network_map.get(native_network_name)
        if not native_id:
            module.fail_json(msg=f"Native network '{native_network_name}' not found", profile=item["name"])
        desired_payload["native_networkconf_id"] = native_id

    tagged_names = item.get("tagged_network_names") or []
    if tagged_names:
        tagged_ids = []
        for name in tagged_names:
            tid = network_map.get(name)
            if not tid:
                module.fail_json(msg=f"Tagged network '{name}' not found", profile=item["name"])
            tagged_ids.append(tid)
        desired_payload["tagged_networkconf_ids"] = tagged_ids

    if item.get("poe_mode"):
        desired_payload["poe_mode"] = item["poe_mode"]
    if item.get("isolation") is not None:
        desired_payload["isolation"] = item["isolation"]

    return desired_payload


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            username=dict(type="str", required=True, no_log=True),
            password=dict(type="str", required=True, no_log=True),
            site=dict(type="str", default="default"),
            validate_certs=dict(type="bool", default=False),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            name=dict(type="str"),
            native_network_name=dict(type="str"),
            tagged_network_names=dict(type="list", elements="str"),
            poe_mode=dict(type="str", choices=["auto", "off", "passthrough"]),
            isolation=dict(type="bool"),
            autoneg=dict(type="bool", default=True),
            profiles=dict(type="list", elements="dict"),
        ),
        supports_check_mode=True,
    )

    desired_items = _normalize_desired(module)

    api = UnifiAPI(
        module, module.params["host"], module.params["username"], module.params["password"], module.params["validate_certs"]
    )
    api.login()
    site = module.params["site"]

    networks_res, info = api.request(f"/proxy/network/api/s/{site}/rest/networkconf")
    networks = _as_data_list(networks_res)
    if not networks:
        module.fail_json(msg="Failed to fetch networks", info=info)
    network_map = {n["name"]: n["_id"] for n in networks if "name" in n and "_id" in n}

    profiles_res, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    profiles = _as_data_list(profiles_res)
    if profiles_res is None:
        module.fail_json(msg="Failed to fetch port profiles", info=info)

    changed = False
    results = []
    by_name = {p.get("name"): p for p in profiles if isinstance(p, dict)}

    for item in desired_items:
        name = item.get("name")
        if not name:
            module.fail_json(msg="Each profile item must include 'name'", item=item)
        state = item.get("state", "present")
        existing = by_name.get(name)
        result_profile = existing
        item_changed = False

        if state == "present":
            desired_payload = _build_payload(module, item, network_map)
            if not existing:
                item_changed = True
                if not module.check_mode:
                    result_profile, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/portconf", method="POST", data=desired_payload
                    )
                    if not result_profile:
                        module.fail_json(msg="Failed to create port profile", info=info, profile=name)
                    by_name[name] = result_profile
            else:
                for key, value in desired_payload.items():
                    if existing.get(key) != value:
                        item_changed = True
                        break
                if item_changed and not module.check_mode:
                    result_profile, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="PUT", data=desired_payload
                    )
                    if not result_profile:
                        module.fail_json(msg="Failed to update port profile", info=info, profile=name)
                    by_name[name] = result_profile
        else:
            if existing:
                item_changed = True
                if not module.check_mode:
                    _, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf/{existing['_id']}", method="DELETE")
                    if info.get("status") not in [200, 204]:
                        module.fail_json(msg="Failed to delete port profile", info=info, profile=name)
                result_profile = None
                by_name.pop(name, None)

        changed = changed or item_changed
        results.append({"name": name, "changed": item_changed, "state": state, "profile": result_profile})

    module.exit_json(changed=changed, results=results)


if __name__ == "__main__":
    run_module()
