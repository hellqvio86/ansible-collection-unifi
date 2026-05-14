#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: unifi_user_certificate
short_description: Manage UniFi OS user certificates via control-plane API
version_added: "0.0.3"
description:
    - Uploads and manages certificates in UniFi OS at /api/userCertificates.
options:
    host:
        type: str
        required: false
    username:
        type: str
        required: false
    password:
        type: str
        required: false
    validate_certs:
        type: bool
        default: false
    state:
        type: str
        choices: [present, absent]
        default: present
    name:
        type: str
        required: false
    cert:
        type: str
    key:
        type: str
    active:
        type: bool
        default: true
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str"),
            username=dict(type="str", no_log=True),
            password=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=False),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            name=dict(type="str", required=True),
            cert=dict(type="str", no_log=True),
            key=dict(type="str", no_log=True),
            active=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )

    state = module.params["state"]
    name = module.params["name"]
    cert = module.params.get("cert")
    key = module.params.get("key")
    active = module.params.get("active", True)

    if state == "present" and (not cert or not key):
        module.fail_json(msg="'cert' and 'key' are required when state=present")

    api = UnifiAPI(module, module.params["host"], module.params["username"], module.params["password"], module.params["validate_certs"])
    api.login()

    existing_res, info = api.request("/api/userCertificates")
    existing_list = api.as_list(existing_res)
    existing = next((c for c in existing_list if c.get("name") == name), None)

    changed = False
    result = existing

    if state == "present":
        if not existing:
            changed = True
            if not module.check_mode:
                payload = {"name": name, "cert": cert, "key": key}
                res, info = api.request("/api/userCertificates", method="POST", data=payload)
                res_list = api.as_list(res)
                result = res_list[0] if res_list else res
                if not result:
                    module.fail_json(msg="Failed to upload user certificate", info=info)
                # Optionally activate uploaded cert for UniFi OS Web UI.
                if active and result.get("id"):
                    status_res, info = api.request(
                        f"/api/userCertificates/{result['id']}/status",
                        method="PUT",
                        data={"active": True},
                    )
                    if not status_res:
                        module.fail_json(msg="Failed to activate uploaded user certificate", info=info, certificate_id=result["id"])
                    result = status_res
                    changed = True
        else:
            result = existing
            # Ensure target cert is active when requested.
            if active and not bool(existing.get("active", False)):
                changed = True
                if not module.check_mode:
                    cert_id = existing.get("id")
                    if not cert_id:
                        module.fail_json(msg="Existing certificate missing id, cannot activate", certificate=existing)
                    status_res, info = api.request(
                        f"/api/userCertificates/{cert_id}/status",
                        method="PUT",
                        data={"active": True},
                    )
                    if not status_res:
                        module.fail_json(msg="Failed to activate existing user certificate", info=info, certificate_id=cert_id)
                    result = status_res
    else:
        if existing:
            changed = True
            if not module.check_mode:
                cert_id = existing.get("id")
                if not cert_id:
                    module.fail_json(msg="Existing certificate missing id, cannot delete", certificate=existing)
                _, info = api.request(f"/api/userCertificates/{cert_id}", method="DELETE")
                if info.get("status") not in [200, 204]:
                    module.fail_json(msg="Failed to delete user certificate", info=info, certificate_id=cert_id)
            result = None

    module.exit_json(changed=changed, certificate=result)


if __name__ == "__main__":
    run_module()
