#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: unifi_ssl_config
short_description: Manage UniFi OS SSL certificates via SSH
version_added: "0.0.1"
description:
    - Deploys SSL certificates (CRT and KEY) to UniFi OS and restarts the core service.
    - Replaces the default self-signed or existing certificates at specified paths.
    - Supports wildcard certificates and ensures idempotency by comparing content before writing.
    - This module modulates the SSH transport logic within the module itself using Paramiko.
options:
    host:
        description: The IP or hostname of the UDM.
        required: false
        type: str
    ssh_username:
        description: SSH username (typically root).
        required: false
        type: str
    ssh_password:
        description: SSH password.
        type: str
    ssh_key:
        description: Path to SSH private key.
        type: str
    cert_content:
        description: Content of the certificate (PEM).
        required: false
        type: str
    key_content:
        description: Content of the private key (PEM).
        required: false
        type: str
    cert_path:
        description: Target path for the certificate.
        default: /data/unifi-core/config/unifi-core.crt
        type: str
    key_path:
        description: Target path for the private key.
        default: /data/unifi-core/config/unifi-core.key
        type: str
    restart_service:
        description: Whether to restart unifi-core.
        default: true
        type: bool
author:
    - hellqvio86 (@hellqvio86)
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import paramiko

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


def run_module():
    module_args = dict(
        host=dict(type="str"),
        ssh_username=dict(type="str"),
        ssh_password=dict(type="str", no_log=True),
        ssh_key=dict(type="str"),
        cert_content=dict(type="str", required=False, no_log=True),
        key_content=dict(type="str", required=False, no_log=True),
        cert_path=dict(type="str", default="/data/unifi-core/config/unifi-core.crt"),
        key_path=dict(type="str", default="/data/unifi-core/config/unifi-core.key"),
        restart_service=dict(type="bool", default=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not HAS_PARAMIKO:
        module.fail_json(msg="paramiko is required for this module")

    host = module.params["host"]
    username = module.params["ssh_username"]
    password = module.params["ssh_password"]
    key_path = module.params["ssh_key"]
    cert_content = module.params["cert_content"]
    key_content = module.params["key_content"]
    target_cert = module.params["cert_path"]
    target_key = module.params["key_path"]

    changed = False

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

        if key_path:
            ssh.connect(host, username=username, key_filename=key_path)
        else:
            ssh.connect(host, username=username, password=password)

        sftp = ssh.open_sftp()

        # Check current cert
        current_cert = ""
        try:
            with sftp.open(target_cert, "r") as f:
                current_cert = f.read().decode("utf-8")
        except OSError:
            pass

        if current_cert.strip() != cert_content.strip():
            changed = True
            if not module.check_mode:
                with sftp.open(target_cert, "w") as f:
                    f.write(cert_content)
                sftp.chmod(target_cert, 0o644)

        # Check current key
        current_key = ""
        try:
            with sftp.open(target_key, "r") as f:
                current_key = f.read().decode("utf-8")
        except OSError:
            pass

        if current_key.strip() != key_content.strip():
            changed = True
            if not module.check_mode:
                with sftp.open(target_key, "w") as f:
                    f.write(key_content)
                sftp.chmod(target_key, 0o600)

        if changed and module.params["restart_service"] and not module.check_mode:
            ssh.exec_command("systemctl restart unifi-core")

        sftp.close()
        ssh.close()

    except Exception as e:
        module.fail_json(msg=f"SSH/SFTP operation failed: {str(e)}")

    module.exit_json(changed=changed)


if __name__ == "__main__":
    run_module()
