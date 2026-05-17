#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_switch_profile_assignment
short_description: Assign Switch Profiles to UniFi Switches
version_added: "0.0.2"
description:
    - Assign or remove switch profiles from UniFi switches.
    - Supports single assignment mode and batch mode.
options:
    host: {type: str, required: false}
    username: {type: str, required: false}
    password: {type: str, required: false}
    site: {type: str, default: default}
    validate_certs: {type: bool, default: false}
    state: {type: str, choices: [present, absent], default: present}
    switch_name: {type: str}
    switch_mac: {type: str}
    switch_ip: {type: str}
    profile_name: {type: str}
    assignments:
        description: Batch input for switch profile assignments.
        type: list
        elements: dict
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def _normalize_desired(module):
    batch = module.params.get("assignments") or []
    if batch:
        return batch
    if not module.params.get("profile_name"):
        module.fail_json(msg="Either 'profile_name' (single mode) or 'assignments' (batch mode) must be provided")
    if not any([module.params.get("switch_name"), module.params.get("switch_mac"), module.params.get("switch_ip")]):
        module.fail_json(msg="At least one of switch_name, switch_mac, or switch_ip must be provided")
    return [
        {
            "state": module.params["state"],
            "profile_name": module.params["profile_name"],
            "switch_name": module.params.get("switch_name"),
            "switch_mac": module.params.get("switch_mac"),
            "switch_ip": module.params.get("switch_ip"),
        }
    ]


def _fetch_switch_profiles(api, site):
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/switchprofile")
    if info.get("status") == 200:
        return api.as_list(res), True
    return [], False


def _fetch_devices(api, site):
    res, info = api.request(f"/proxy/network/api/s/{site}/rest/device")
    if info.get("status") == 200:
        return api.as_list(res)
    res, info = api.request(f"/proxy/network/api/s/{site}/stat/device")
    if info.get("status") == 200:
        return api.as_list(res)
    return []


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str"),
            username=dict(type="str", no_log=True),
            password=dict(type="str", no_log=True),
            site=dict(type="str", default="default"),
            validate_certs=dict(type="bool", default=False),
            unifi_session_cookie=dict(type="str", no_log=True, required=False),
            unifi_csrf_token=dict(type="str", no_log=True, required=False),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            switch_name=dict(type="str"),
            switch_mac=dict(type="str"),
            switch_ip=dict(type="str"),
            profile_name=dict(type="str"),
            assignments=dict(type="list", elements="dict"),
        ),
        supports_check_mode=True,
    )

    desired_items = _normalize_desired(module)
    api = UnifiAPI(
        module, module.params["host"], module.params["username"], module.params["password"], module.params["validate_certs"],
        module.params.get("unifi_session_cookie"),
        module.params.get("unifi_csrf_token"),
    )
    api.login()
    site = module.params["site"]

    switch_profiles, switchprofile_supported = _fetch_switch_profiles(api, site)
    if not switchprofile_supported:
        module.exit_json(
            changed=False,
            results=[],
            switchprofile_api_supported=False,
            skipped_assignments=[i.get("profile_name") for i in desired_items],
            msg="Switch profile API unsupported on this controller; assignments skipped.",
        )

    profile_map = {p["name"]: p["_id"] for p in switch_profiles if isinstance(p, dict) and "name" in p and "_id" in p}
    devices = _fetch_devices(api, site)
    if not devices:
        module.fail_json(msg="Failed to fetch devices from rest/device and stat/device endpoints")

    changed = False
    results = []
    switches = [d for d in devices if isinstance(d, dict) and d.get("type") == "usw"]

    for item in desired_items:
        profile_name = item.get("profile_name")
        if not profile_name:
            module.fail_json(msg="Each assignment item must include 'profile_name'", item=item)
        if profile_name not in profile_map:
            module.fail_json(msg=f"Switch profile '{profile_name}' not found", assignment=item)
        profile_id = profile_map[profile_name]

        target = None
        for sw in switches:
            if item.get("switch_name") and sw.get("name") == item["switch_name"]:
                target = sw
                break
            if item.get("switch_mac") and sw.get("mac") == item["switch_mac"]:
                target = sw
                break
            if item.get("switch_ip") and sw.get("ip") == item["switch_ip"]:
                target = sw
                break

        if not target:
            module.fail_json(msg="Switch not found with provided identifiers", assignment=item)

        switch_id = target["_id"]
        current_profile_id = target.get("switch_profile_id")
        desired_state = item.get("state", "present")
        item_changed = False

        if desired_state == "present":
            if current_profile_id != profile_id:
                item_changed = True
                if not module.check_mode:
                    res, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/device/{switch_id}",
                        method="PUT",
                        data={"switch_profile_id": profile_id},
                    )
                    res_list = api.as_list(res)
                    result_dev = res_list[0] if res_list else res
                    if not result_dev:
                        module.fail_json(msg="Failed to assign switch profile", info=info, assignment=item)
                    target = result_dev
        else:
            if current_profile_id is not None:
                item_changed = True
                if not module.check_mode:
                    res, info = api.request(
                        f"/proxy/network/api/s/{site}/rest/device/{switch_id}",
                        method="PUT",
                        data={"switch_profile_id": None},
                    )
                    res_list = api.as_list(res)
                    result_dev = res_list[0] if res_list else res
                    if not result_dev:
                        module.fail_json(msg="Failed to remove switch profile assignment", info=info, assignment=item)
                    target = result_dev

        changed = changed or item_changed
        results.append({"assignment": item, "changed": item_changed, "switch": target})

    module.exit_json(changed=changed, results=results, switchprofile_api_supported=True)


if __name__ == "__main__":
    run_module()
