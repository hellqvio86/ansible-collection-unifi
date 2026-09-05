# MIT License (see LICENSE.md)

import datetime
import os
import re
from typing import Any

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

try:
    import paramiko

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


def get_cert_validity(cert: Any) -> tuple[datetime.datetime, datetime.datetime]:
    """Extract UTC-aware not_valid_before and not_valid_after from an x509 certificate."""
    if hasattr(cert, "not_valid_before_utc"):
        nvb = cert.not_valid_before_utc
    else:
        nvb = cert.not_valid_before.replace(tzinfo=datetime.timezone.utc)

    if hasattr(cert, "not_valid_after_utc"):
        nva = cert.not_valid_after_utc
    else:
        nva = cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)

    return nvb, nva


def validate_pem_cert(cert_content: str) -> tuple[bool, str, list[Any]]:
    """Validate PEM certificate syntax and load certificates.

    Returns (is_valid, error_message, cert_objects).
    """
    if not cert_content or not isinstance(cert_content, str):
        return False, "Certificate content is empty or not a string.", []

    cert_str = cert_content.strip()
    if "-----BEGIN CERTIFICATE-----" not in cert_str or "-----END CERTIFICATE-----" not in cert_str:
        return False, "Invalid PEM certificate: missing BEGIN or END CERTIFICATE delimiters.", []

    if not HAS_CRYPTOGRAPHY:
        return False, "cryptography library is required for SSL certificate validation.", []

    try:
        certs = x509.load_pem_x509_certificates(cert_str.encode("utf-8"))
        if not certs:
            return False, "No valid x509 certificates found in certificate content.", []
        return True, "", certs
    except Exception as e:
        return False, f"Failed to parse x509 certificate: {e}", []


def validate_pem_key(key_content: str) -> tuple[bool, str, Any]:
    """Validate PEM private key syntax and load private key.

    Returns (is_valid, error_message, key_object).
    """
    if not key_content or not isinstance(key_content, str):
        return False, "Private key content is empty or not a string.", None

    key_str = key_content.strip()
    if "-----BEGIN " not in key_str or "KEY-----" not in key_str:
        return False, "Invalid PEM private key: missing BEGIN or END KEY delimiters.", None

    if not HAS_CRYPTOGRAPHY:
        return False, "cryptography library is required for SSL key validation.", None

    try:
        private_key = serialization.load_pem_private_key(key_str.encode("utf-8"), password=None)
        return True, "", private_key
    except Exception as e:
        return False, f"Failed to parse PEM private key: {e}", None


def verify_cert_key_pair(leaf_cert: Any, private_key: Any) -> tuple[bool, str]:
    """Verify that a leaf certificate's public key matches the provided private key."""
    if not HAS_CRYPTOGRAPHY:
        return False, "cryptography library is required for SSL key pairing verification."

    try:
        cert_pub_bytes = leaf_cert.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_pub_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if cert_pub_bytes != key_pub_bytes:
            return False, "Certificate public key does not match the provided private key."
        return True, ""
    except Exception as e:
        return False, f"Error verifying certificate/key pairing: {e}"


def validate_cert_chain(certs: list[Any]) -> tuple[bool, str]:
    """Validate certificate chain structure if multiple certificates are present."""
    if len(certs) <= 1:
        return True, ""

    for i in range(len(certs) - 1):
        child = certs[i]
        issuer_candidate = certs[i + 1]
        if child.issuer != issuer_candidate.subject:
            return (
                False,
                f"Certificate chain broken at index {i}: issuer '{child.issuer.rfc4514_string()}' does not match next subject '{issuer_candidate.subject.rfc4514_string()}'.",
            )
    return True, ""


def check_cert_dates(certs: list[Any], warning_days: int = 30) -> tuple[bool, str, list[str]]:
    """Check validity dates of certificates in the chain.

    Returns (is_valid, error_msg, warnings_list).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    warnings: list[str] = []

    for idx, cert in enumerate(certs):
        nvb, nva = get_cert_validity(cert)
        subject_name = cert.subject.rfc4514_string() or f"cert[{idx}]"
        if now < nvb:
            return (
                False,
                f"Certificate '{subject_name}' is not yet valid (valid from {nvb.isoformat()}).",
                warnings,
            )
        if now > nva:
            return (
                False,
                f"Certificate '{subject_name}' has expired on {nva.isoformat()}.",
                warnings,
            )
        if now <= nva <= now + datetime.timedelta(days=warning_days):
            warnings.append(
                f"Certificate '{subject_name}' expires soon on {nva.isoformat()} (within {warning_days} days)."
            )

    return True, "", warnings


def sanitize_ssh_error(
    err: Exception,
    host: str = "",
    username: str = "",
    secrets: list[str] | None = None,
) -> str:
    """Sanitize error messages from SSH and SFTP operations to avoid leaking credentials or keys."""
    if HAS_PARAMIKO:
        if isinstance(err, paramiko.AuthenticationException):
            return f"SSH authentication failed for user '{username}' on host '{host}'."
        if isinstance(err, paramiko.BadHostKeyException):
            return f"SSH host key verification failed: host key does not match known_hosts for '{host}'."

    err_msg = str(err)

    for secret in secrets or []:
        if secret and secret in err_msg:
            err_msg = err_msg.replace(secret, "********")

    # Redact private keys (PKCS#1, PKCS#8, etc.)
    err_msg = re.sub(
        r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----",
        "[PRIVATE KEY REDACTED]",
        err_msg,
        flags=re.IGNORECASE,
    )
    # Redact certificates
    err_msg = re.sub(
        r"-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----",
        "[CERTIFICATE REDACTED]",
        err_msg,
        flags=re.IGNORECASE,
    )
    # Redact sensitive parameters in key-value pairs
    err_msg = re.sub(
        r"(?i)\b(password|token|key|secret)\b(\s*[:=]\s*)([\"']?)([^\s,\"']+)([\"']?)",
        r"\1\2\3********\5",
        err_msg,
    )
    # Redact local filesystem paths containing private keys
    err_msg = re.sub(
        r"(/[^ \t\n\r\f\v]+(?:\.(?:pem|key|crt)|id_rsa|id_ed25519|id_ecdsa|id_dsa)[^ \t\n\r\f\v]*)",
        "[KEY_PATH_REDACTED]",
        err_msg,
    )
    return err_msg


def atomic_sftp_replace(sftp: Any, remote_path: str, content: str, mode: int = 0o644) -> None:
    """Safely replace a remote file over SFTP using atomic posix_rename with backup-before-replace fallback.

    Ensures that an existing known-good certificate or key file is never lost if rename fails.
    """
    tmp_path = f"{remote_path}.tmp.{os.getpid()}"
    bak_path = f"{remote_path}.bak.{os.getpid()}"

    # Step 1: Write temporary file and set mode
    try:
        with sftp.open(tmp_path, "w") as f:
            f.write(content)
        sftp.chmod(tmp_path, mode)
    except Exception as e:
        try:
            sftp.remove(tmp_path)
        except OSError:
            pass
        raise OSError(f"Failed writing temporary file {tmp_path}: {e}") from e

    # Step 2: Try atomic POSIX rename
    posix_rename_success = False
    try:
        sftp.posix_rename(tmp_path, remote_path)
        posix_rename_success = True
    except (AttributeError, OSError):
        posix_rename_success = False

    if not posix_rename_success:
        # Step 3: Fallback with backup-before-replace strategy
        has_backup = False
        try:
            sftp.stat(remote_path)
            sftp.rename(remote_path, bak_path)
            has_backup = True
        except OSError:
            has_backup = False

        try:
            sftp.rename(tmp_path, remote_path)
        except Exception as rename_err:
            # Rollback: restore backup file if available
            if has_backup:
                try:
                    sftp.rename(bak_path, remote_path)
                except Exception:
                    pass
            try:
                sftp.remove(tmp_path)
            except OSError:
                pass
            raise OSError(
                f"Failed to replace {remote_path}; restored previous file from backup: {rename_err}"
            ) from rename_err

        # Cleanup backup after successful replacement
        if has_backup:
            try:
                sftp.remove(bak_path)
            except OSError:
                pass

    # Step 4: Verify file exists and permissions after write
    try:
        remote_stat = sftp.stat(remote_path)
        remote_mode = remote_stat.st_mode & 0o777
        if remote_mode != mode:
            sftp.chmod(remote_path, mode)
    except Exception as verify_err:
        raise OSError(f"Failed verifying remote file {remote_path} after write: {verify_err}") from verify_err
