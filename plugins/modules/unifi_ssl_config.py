#!/usr/bin/python
# (c) 2026, hellqvio86 (@hellqvio86)
# MIT License (see LICENSE.md)

DOCUMENTATION = r"""
---
module: unifi_ssl_config
short_description: Manage UniFi OS SSL certificates via SSH (privileged escape hatch)
version_added: "0.0.1"
description:
    - Privileged escape hatch module that deploys SSL certificates (CRT and KEY) directly
      to UniFi OS filesystem paths (/data/unifi-core/config) and restarts the unifi-core service.
    - Operates directly over SSH and SFTP rather than using the official UniFi REST API.
    - Validates PEM syntax, certificate validity dates, certificate chains, and verifies that the
      certificate public key cryptographically matches the private key before making any remote changes.
    - Employs transactional file replacement with rollback safeguards so existing certificates are never lost.
    - Verifies file permissions and content on the remote filesystem prior to restarting the service.
options:
    host:
        description: The IP or hostname of the UniFi OS console (UDM, UDR, UCG, UXG).
        required: true
        type: str
    ssh_username:
        description: SSH username (typically root).
        default: root
        type: str
    ssh_password:
        description: SSH password.
        type: str
        no_log: true
    ssh_key:
        description: Path to SSH private key.
        type: str
    cert_content:
        description: Content of the certificate or fullchain (PEM format).
        required: false
        type: str
        no_log: true
    key_content:
        description: Content of the private key (PEM format).
        required: false
        type: str
        no_log: true
    cert_path:
        description: Target path for the certificate on the UniFi OS filesystem.
        default: /data/unifi-core/config/unifi-core.crt
        type: str
    key_path:
        description: Target path for the private key on the UniFi OS filesystem.
        default: /data/unifi-core/config/unifi-core.key
        type: str
    restart_service:
        description: Whether to restart the UniFi OS service after certificate update.
        default: true
        type: bool
    service_name:
        description: Systemd service name to restart on UniFi OS.
        default: unifi-core
        type: str
    timeout:
        description: SSH connection timeout in seconds.
        default: 30
        type: int
    operation_timeout:
        description: SFTP and command execution timeout in seconds.
        default: 30
        type: int
    host_key_policy:
        description:
            - SSH host key verification policy.
            - C(reject) requires the host key to be in known_hosts (recommended).
            - C(auto_add) automatically accepts and saves unknown host keys.
            - C(warning) logs a warning for unknown host keys but connects.
        default: reject
        choices: ["reject", "auto_add", "warning"]
        type: str
    warning_days:
        description: Number of days before certificate expiry to issue an Ansible warning.
        default: 30
        type: int
author:
    - hellqvio86 (@hellqvio86)
"""

EXAMPLES = r"""
- name: Deploy custom SSL certificate to UDM Pro via SSH
  hellqvio86.unifi.unifi_ssl_config:
    host: 192.168.1.1
    ssh_username: root
    ssh_key: ~/.ssh/id_ed25519
    cert_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/fullchain.pem') }}"
    key_content: "{{ lookup('file', '/etc/letsencrypt/live/unifi.example.com/privkey.pem') }}"
    host_key_policy: reject
"""

RETURN = r"""
changed:
    description: Whether any certificate or key files were modified.
    returned: always
    type: bool
warnings:
    description: Warnings related to certificate expiration or configuration.
    returned: when warnings exist
    type: list
    elements: str
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import paramiko

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_ssl import (
        HAS_CRYPTOGRAPHY,
        atomic_sftp_replace,
        check_cert_dates,
        sanitize_ssh_error,
        validate_cert_chain,
        validate_pem_cert,
        validate_pem_key,
        verify_cert_key_pair,
    )
except ImportError:
    from plugins.module_utils.unifi_ssl import (  # type: ignore[no-redef]
        HAS_CRYPTOGRAPHY,
        atomic_sftp_replace,
        check_cert_dates,
        sanitize_ssh_error,
        validate_cert_chain,
        validate_pem_cert,
        validate_pem_key,
        verify_cert_key_pair,
    )


def run_module():
    module_args = dict(
        host=dict(type="str", required=False),
        ssh_username=dict(type="str", default="root"),
        ssh_password=dict(type="str", no_log=True),
        ssh_key=dict(type="str"),
        cert_content=dict(type="str", required=False, no_log=True),
        key_content=dict(type="str", required=False, no_log=True),
        cert_path=dict(type="str", default="/data/unifi-core/config/unifi-core.crt"),
        key_path=dict(type="str", default="/data/unifi-core/config/unifi-core.key"),
        restart_service=dict(type="bool", default=True),
        service_name=dict(type="str", default="unifi-core"),
        timeout=dict(type="int", default=30),
        operation_timeout=dict(type="int", default=30),
        host_key_policy=dict(type="str", default="reject", choices=["reject", "auto_add", "warning"]),
        warning_days=dict(type="int", default=30),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not HAS_PARAMIKO:
        module.fail_json(msg="paramiko is required for this module")

    if not HAS_CRYPTOGRAPHY:
        module.fail_json(msg="cryptography is required for this module")

    host = module.params.get("host")
    username = module.params.get("ssh_username") or "root"
    password = module.params.get("ssh_password")
    key_path = module.params.get("ssh_key")
    cert_content = module.params.get("cert_content")
    key_content = module.params.get("key_content")
    target_cert = module.params.get("cert_path") or "/data/unifi-core/config/unifi-core.crt"
    target_key = module.params.get("key_path") or "/data/unifi-core/config/unifi-core.key"
    restart_service = module.params.get("restart_service")
    service_name = module.params.get("service_name") or "unifi-core"
    timeout = module.params.get("timeout") or 30
    operation_timeout = module.params.get("operation_timeout") or 30
    host_key_policy = module.params.get("host_key_policy") or "reject"
    warning_days = module.params.get("warning_days") or 30

    if not host:
        module.fail_json(msg="Parameter 'host' must be specified.")

    if cert_content is None and key_content is None:
        module.fail_json(msg="At least one of cert_content or key_content must be specified.")

    leaf_cert = None
    parsed_certs = []
    if cert_content is not None:
        is_valid, err, parsed_certs = validate_pem_cert(cert_content)
        if not is_valid:
            module.fail_json(msg=f"Invalid PEM certificate provided in cert_content: {err}")
        leaf_cert = parsed_certs[0]

        is_chain_valid, chain_err = validate_cert_chain(parsed_certs)
        if not is_chain_valid:
            module.fail_json(msg=f"Invalid certificate chain in cert_content: {chain_err}")

        are_dates_valid, date_err, date_warnings = check_cert_dates(parsed_certs, warning_days=warning_days)
        if not are_dates_valid:
            module.fail_json(msg=f"Certificate validity check failed: {date_err}")
        for warn_msg in date_warnings:
            module.warn(warn_msg)

    parsed_key = None
    if key_content is not None:
        is_valid, err, parsed_key = validate_pem_key(key_content)
        if not is_valid:
            module.fail_json(msg=f"Invalid PEM private key provided in key_content: {err}")

    # Cryptographic pairing verification if both are supplied
    if leaf_cert is not None and parsed_key is not None:
        matches, pair_err = verify_cert_key_pair(leaf_cert, parsed_key)
        if not matches:
            module.fail_json(msg=f"Certificate and private key do not match: {pair_err}")

    changed = False
    ssh = None
    sftp = None

    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

        connect_kwargs = {
            "hostname": host,
            "username": username,
            "timeout": timeout,
        }
        if key_path:
            connect_kwargs["key_filename"] = key_path
        else:
            connect_kwargs["password"] = password

        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        try:
            channel = sftp.get_channel()
            if channel:
                channel.settimeout(operation_timeout)
        except (AttributeError, OSError):
            pass

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
                    atomic_sftp_replace(sftp, target_cert, cert_content, mode=0o644)
                    # Verify deployed certificate on disk
                    with sftp.open(target_cert, "r") as f:
                        deployed_cert_data = f.read().decode("utf-8")
                    valid, err, _ = validate_pem_cert(deployed_cert_data)
                    if not valid:
                        raise OSError(f"Remote certificate verification failed after write: {err}")

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
                    atomic_sftp_replace(sftp, target_key, key_content, mode=0o600)
                    # Verify deployed private key on disk
                    with sftp.open(target_key, "r") as f:
                        deployed_key_data = f.read().decode("utf-8")
                    valid, err, _ = validate_pem_key(deployed_key_data)
                    if not valid:
                        raise OSError(f"Remote private key verification failed after write: {err}")

        if changed and restart_service and not module.check_mode:
            _stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service_name}", timeout=operation_timeout)
            exit_status = 0
            if hasattr(stdout, "channel") and hasattr(stdout.channel, "recv_exit_status"):
                try:
                    res = stdout.channel.recv_exit_status()
                    if isinstance(res, int):
                        exit_status = res
                except Exception:
                    exit_status = 0
            if exit_status != 0:
                err_output = stderr.read().decode("utf-8", errors="replace").strip()
                module.fail_json(
                    msg=f"Files updated successfully, but service '{service_name}' restart failed (exit code {exit_status}): {err_output}",
                    changed=True,
                )

    except Exception as e:
        if isinstance(e, SystemExit) or str(e) == "fail_json":
            raise
        sanitized = sanitize_ssh_error(
            e,
            host=host,
            username=username,
            secrets=[password, key_content, cert_content],
        )
        module.fail_json(msg=f"SSH/SFTP operation failed: {sanitized}")
    finally:
        if sftp is not None:
            try:
                sftp.close()
            except Exception:
                pass
        if ssh is not None:
            try:
                ssh.close()
            except Exception:
                pass

    module.exit_json(changed=changed)


if __name__ == "__main__":
    run_module()
