#!/usr/bin/python

DOCUMENTATION = r"""
---
module: unifi_switch_profile
short_description: Manage UniFi Switch Profiles
version_added: "0.0.2"
description:
    - Create, update, or delete switch profiles in a UniFi controller.
    - Supports single profile mode and batch mode.
options:
    host: {type: str, required: true}
    username: {type: str, required: true}
    password: {type: str, required: true}
    site: {type: str, default: default}
    validate_certs: {type: bool, default: false}
    state: {type: str, choices: [present, absent], default: present}
    name: {type: str}
    model: {type: str}
    port_profile_overrides: {type: dict}
    description: {type: str}
    profiles:
        description: Batch input for switch profiles.
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
            "model": module.params.get("model"),
            "port_profile_overrides": module.params.get("port_profile_overrides"),
            "description": module.params.get("description"),
        }
    ]


def _fetch_switch_profiles(api, site):
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile")
    if info.get("status") == 200:
        return _as_data_list(res), info, True
    # Fallback for controllers that expose switchconf read path.
    res_fb, info_fb = api.request(f"/proxy/network/api/s/{site}/rest/switchconf")
    if info_fb.get("status") == 200:
        return _as_data_list(res_fb), info_fb, False
    return [], info, False


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
            model=dict(type="str"),
            port_profile_overrides=dict(type="dict"),
            description=dict(type="str"),
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

    port_profiles_res, info = api.request(f"/proxy/network/api/s/{site}/rest/portconf")
    port_profiles = _as_data_list(port_profiles_res)
    if port_profiles_res is None:
        module.fail_json(msg="Failed to fetch port profiles", info=info)
    port_profile_map = {p["name"]: p["_id"] for p in port_profiles if "name" in p and "_id" in p}

    switch_profiles, info, write_supported = _fetch_switch_profiles(api, site)
    by_name = {p.get("name"): p for p in switch_profiles if isinstance(p, dict)}

    changed = False
    results = []
    skipped = []

    for item in desired_items:
        name = item.get("name")
        if not name:
            module.fail_json(msg="Each profile item must include 'name'", item=item)
        state = item.get("state", "present")
        existing = by_name.get(name)
        result_profile = existing
        item_changed = False

        port_overrides = {}
        for port_num, profile_name in (item.get("port_profile_overrides") or {}).items():
            if profile_name not in port_profile_map:
                module.fail_json(msg=f"Port profile '{profile_name}' not found", profile=name)
            port_overrides[int(port_num)] = port_profile_map[profile_name]

        desired_payload = {"name": name}
        if item.get("model"):
            desired_payload["model"] = item["model"]
        if port_overrides:
            desired_payload["port_overrides"] = port_overrides
        if item.get("description"):
            desired_payload["description"] = item["description"]

        # If controller doesn't support switchprofile writes, skip cleanly.
        if not write_supported:
            skipped.append(name)
            results.append({"name": name, "changed": False, "state": state, "skipped": True, "reason": "switchprofile_api_unsupported"})
            continue

        if state == "present":
            if not existing:
                item_changed = True
                if not module.check_mode:
                    result_profile, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/switchprofile", method="POST", data=desired_payload
                    )
                    if not result_profile:
                        module.fail_json(msg="Failed to create switch profile", info=info, profile=name)
                    by_name[name] = result_profile
            else:
                for key, value in desired_payload.items():
                    if existing.get(key) != value:
                        item_changed = True
                        break
                if item_changed and not module.check_mode:
                    result_profile, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}", method="PUT", data=desired_payload
                    )
                    if not result_profile:
                        module.fail_json(msg="Failed to update switch profile", info=info, profile=name)
                    by_name[name] = result_profile
        else:
            if existing:
                item_changed = True
                if not module.check_mode:
                    _, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile/{existing['_id']}", method="DELETE")
                    if info.get("status") not in [200, 204]:
                        module.fail_json(msg="Failed to delete switch profile", info=info, profile=name)
                result_profile = None
                by_name.pop(name, None)

        changed = changed or item_changed
        results.append({"name": name, "changed": item_changed, "state": state, "profile": result_profile})

    module.exit_json(changed=changed, results=results, switchprofile_api_supported=write_supported, skipped_profiles=skipped)


if __name__ == "__main__":
    run_module()
