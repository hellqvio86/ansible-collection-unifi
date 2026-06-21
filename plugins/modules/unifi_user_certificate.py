#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_user_certificate
short_description: Manage UniFi OS user certificates via control-plane API
version_added: "0.0.17"
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
            site=dict(type="str", default="default"),
            validate_certs=dict(type="bool", default=False),
            unifi_session_cookie=dict(type="str", no_log=True, required=False),
            unifi_csrf_token=dict(type="str", no_log=True, required=False),
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

    existing_res, info = api.request("/api/userCertificates")
    existing_list = api.as_list(existing_res)

    # Compute fingerprint of local PEM certificate if we are in present state
    local_fingerprint = None
    if state == "present":
        try:
            import hashlib
            import ssl
            # Extract only the first certificate (leaf) in the PEM chain
            first_pem = cert.split("-----END CERTIFICATE-----")[0] + "-----END CERTIFICATE-----"
            der_cert = ssl.PEM_cert_to_DER_cert(first_pem)
            local_fingerprint = ":".join(
                hashlib.sha1(der_cert).hexdigest()[i:i+2] for i in range(0, 40, 2)
            ).upper()
        except Exception as e:
            module.fail_json(msg="Failed to compute certificate fingerprint: " + str(e))

    changed = False
    result = None

    if state == "present":
        # Check if there is an existing certificate with the same fingerprint
        matching_fp_cert = next(
            (c for c in existing_list if c.get("fingerprint", "").upper() == local_fingerprint),
            None
        )

        if matching_fp_cert:
            # Certificate is already uploaded!
            result = matching_fp_cert
            if active and not bool(matching_fp_cert.get("active", False)):
                changed = True
                if not module.check_mode:
                    cert_id = matching_fp_cert.get("id")
                    status_res, info = api.request(
                        f"/api/userCertificates/{cert_id}/status",
                        method="PUT",
                        data={"active": True},
                    )
                    if not status_res:
                        module.fail_json(
                            msg="Failed to activate existing user certificate", info=info, certificate_id=cert_id
                        )
                    result = status_res
            
            # Clean up other inactive certificates starting with name prefix
            if not module.check_mode:
                active_id = result.get("id")
                for c in existing_list:
                    c_name = c.get("name", "")
                    c_id = c.get("id")
                    if c_id and c_id != active_id and c_name.startswith(name) and not bool(c.get("active", False)):
                        api.request(f"/api/userCertificates/{c_id}", method="DELETE")
        else:
            # Certificate is NOT on the UDM. We need to upload it.
            # Use a unique name format: {name}-{short_fingerprint} to prevent name conflicts
            short_fp = local_fingerprint.replace(":", "").lower()[:8]
            upload_name = f"{name}-{short_fp}"
            
            # Delete any existing inactive certificate with this upload_name first if it somehow exists
            if not module.check_mode:
                for c in existing_list:
                    if c.get("name") == upload_name and not bool(c.get("active", False)):
                        c_id = c.get("id")
                        if c_id:
                            api.request(f"/api/userCertificates/{c_id}", method="DELETE")
            
            changed = True
            if not module.check_mode:
                payload = {"name": upload_name, "cert": cert, "key": key}
                res, info = api.request("/api/userCertificates", method="POST", data=payload)
                res_list = api.as_list(res)
                new_cert = res_list[0] if res_list else res
                if not new_cert:
                    module.fail_json(msg="Failed to upload user certificate", info=info)
                new_id = new_cert.get("id")
                
                # Activate the uploaded cert
                if active and new_id:
                    status_res, info = api.request(
                        f"/api/userCertificates/{new_id}/status",
                        method="PUT",
                        data={"active": True},
                    )
                    if not status_res:
                        module.fail_json(
                            msg="Failed to activate uploaded user certificate", info=info, certificate_id=new_id
                        )
                    result = status_res
                else:
                    result = new_cert

                # Clean up any other inactive certificates starting with name prefix
                active_id = result.get("id")
                for c in existing_list:
                    c_name = c.get("name", "")
                    c_id = c.get("id")
                    if c_id and c_id != active_id and c_name.startswith(name) and not bool(c.get("active", False)):
                        api.request(f"/api/userCertificates/{c_id}", method="DELETE")
            else:
                result = {"name": upload_name, "fingerprint": local_fingerprint, "active": active}
    else:
        # Find any certificates that start with 'name'
        to_delete = [c for c in existing_list if c.get("name", "").startswith(name)]
        if to_delete:
            changed = True
            if not module.check_mode:
                for c in to_delete:
                    cert_id = c.get("id")
                    if cert_id:
                        _, info = api.request(f"/api/userCertificates/{cert_id}", method="DELETE")
                        if info.get("status") not in [200, 204]:
                            module.fail_json(msg="Failed to delete user certificate", info=info, certificate_id=cert_id)
            result = None

    module.exit_json(changed=changed, certificate=result)


if __name__ == "__main__":
    run_module()
