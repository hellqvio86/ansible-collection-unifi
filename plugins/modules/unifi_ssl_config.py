#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)


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

import os

from ansible.module_utils.basic import AnsibleModule

try:
    import paramiko

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def _validate_pem_cert(cert_content: str) -> bool:
    if not cert_content or not isinstance(cert_content, str):
        return False
    cert_str = cert_content.strip()
    if "-----BEGIN CERTIFICATE-----" not in cert_str or "-----END CERTIFICATE-----" not in cert_str:
        return False
    if HAS_CRYPTOGRAPHY:
        try:
            certs = x509.load_pem_x509_certificates(cert_str.encode("utf-8"))
            return len(certs) > 0
        except Exception:
            return False
    return True


def _validate_pem_key(key_content: str) -> bool:
    if not key_content or not isinstance(key_content, str):
        return False
    key_str = key_content.strip()
    if "-----BEGIN " not in key_str or "KEY-----" not in key_str:
        return False
    if HAS_CRYPTOGRAPHY:
        try:
            serialization.load_pem_private_key(key_str.encode("utf-8"), password=None)
            return True
        except Exception:
            return False
    return True


def _atomic_sftp_write(sftp, remote_path: str, content: str, mode: int):
    tmp_path = f"{remote_path}.tmp.{os.getpid()}"
    try:
        with sftp.open(tmp_path, "w") as f:
            f.write(content)
        sftp.chmod(tmp_path, mode)
        try:
            sftp.posix_rename(tmp_path, remote_path)
        except (AttributeError, OSError):
            try:
                sftp.remove(remote_path)
            except OSError:
                pass
            sftp.rename(tmp_path, remote_path)
    except Exception:
        try:
            sftp.remove(tmp_path)
        except OSError:
            pass
        raise


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

    host = module.params.get("host")
    username = module.params.get("ssh_username")
    password = module.params.get("ssh_password")
    key_path = module.params.get("ssh_key")
    cert_content = module.params.get("cert_content")
    key_content = module.params.get("key_content")
    target_cert = module.params.get("cert_path") or "/data/unifi-core/config/unifi-core.crt"
    target_key = module.params.get("key_path") or "/data/unifi-core/config/unifi-core.key"

    if cert_content is None and key_content is None:
        module.fail_json(msg="At least one of cert_content or key_content must be specified.")

    if cert_content is not None and not _validate_pem_cert(cert_content):
        module.fail_json(msg="Invalid PEM certificate provided in cert_content.")

    if key_content is not None and not _validate_pem_key(key_content):
        module.fail_json(msg="Invalid PEM private key provided in key_content.")

    changed = False

    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

        if key_path:
            ssh.connect(host, username=username, key_filename=key_path)
        else:
            ssh.connect(host, username=username, password=password)

        sftp = ssh.open_sftp()

        # Check and update certificate if provided
        if cert_content is not None:
            current_cert = ""
            try:
                with sftp.open(target_cert, "r") as f:
                    current_cert = f.read().decode("utf-8")
            except OSError:
                pass

            if current_cert.strip() != cert_content.strip():
                changed = True
                if not module.check_mode:
                    _atomic_sftp_write(sftp, target_cert, cert_content, 0o644)

        # Check and update private key if provided
        if key_content is not None:
            current_key = ""
            try:
                with sftp.open(target_key, "r") as f:
                    current_key = f.read().decode("utf-8")
            except OSError:
                pass

            if current_key.strip() != key_content.strip():
                changed = True
                if not module.check_mode:
                    _atomic_sftp_write(sftp, target_key, key_content, 0o600)

        if changed and module.params["restart_service"] and not module.check_mode:
            ssh.exec_command("systemctl restart unifi-core")

        sftp.close()
        ssh.close()

    except Exception as e:
        module.fail_json(msg=f"SSH/SFTP operation failed: {str(e)}")

    module.exit_json(changed=changed)


if __name__ == "__main__":
    run_module()
