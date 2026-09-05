from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import paramiko
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.x509.oid import NameOID

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config import run_module


def create_test_pair(
    key_type="rsa",
    days_valid=90,
    offset_days=0,
    cn="test.example.com",
    issuer=None,
    issuer_key=None,
):
    if key_type == "rsa":
        k = rsa.generate_private_key(65537, 2048)
    elif key_type == "ecdsa":
        k = ec.generate_private_key(ec.SECP256R1())
    elif key_type == "ed25519":
        k = ed25519.Ed25519PrivateKey.generate()
    else:
        raise ValueError(f"Unknown key type: {key_type}")

    now = datetime.now(timezone.utc)
    nvb = now + timedelta(days=offset_days)
    nva = nvb + timedelta(days=days_valid)

    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    iss = issuer if issuer else subj
    sign_k = issuer_key if issuer_key else k

    builder = (
        x509.CertificateBuilder()
        .subject_name(subj)
        .issuer_name(iss)
        .public_key(k.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(nvb)
        .not_valid_after(nva)
    )

    if key_type == "ed25519" or isinstance(sign_k, ed25519.Ed25519PrivateKey):
        c = builder.sign(sign_k, None)
    else:
        c = builder.sign(sign_k, hashes.SHA256())

    cpem = c.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    kpem = k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    return cpem, kpem


# Pre-generate standard test fixtures
_fixture_rsa = create_test_pair("rsa", cn="rsa.example.com")
RSA_CERT = _fixture_rsa[0]
RSA_KEY = _fixture_rsa[1]

_fixture_other_rsa = create_test_pair("rsa", cn="other.example.com")
OTHER_RSA_CERT = _fixture_other_rsa[0]
OTHER_RSA_KEY = _fixture_other_rsa[1]

_fixture_ecdsa = create_test_pair("ecdsa", cn="ecdsa.example.com")
ECDSA_CERT = _fixture_ecdsa[0]
ECDSA_KEY = _fixture_ecdsa[1]

_fixture_ed25519 = create_test_pair("ed25519", cn="ed25519.example.com")
ED25519_CERT = _fixture_ed25519[0]
ED25519_KEY = _fixture_ed25519[1]

_fixture_expired = create_test_pair("rsa", days_valid=10, offset_days=-60, cn="expired.example.com")
EXPIRED_CERT = _fixture_expired[0]
EXPIRED_KEY = _fixture_expired[1]

_fixture_future = create_test_pair("rsa", days_valid=30, offset_days=10, cn="future.example.com")
FUTURE_CERT = _fixture_future[0]
FUTURE_KEY = _fixture_future[1]

_fixture_near = create_test_pair("rsa", days_valid=15, offset_days=-1, cn="near.example.com")
NEAR_CERT = _fixture_near[0]
NEAR_KEY = _fixture_near[1]


def setup_mock_sftp(mock_sftp, initial_files=None):
    files = dict(initial_files or {})

    def _open(path, mode="r"):
        m = MagicMock()
        m.__enter__.return_value = m
        if "w" in mode:

            def _write(data):
                files[path] = data

            m.write.side_effect = _write
        else:
            if path in files:
                content = files[path]
                if isinstance(content, str):
                    content = content.encode("utf-8")
                m.read.return_value = content
            else:
                raise OSError(f"File not found: {path}")
        return m

    def _rename(src, dst):
        if src in files:
            files[dst] = files.pop(src)

    def _stat(path):
        if path in files:
            return MagicMock(st_mode=0o100644)
        raise OSError(f"No such file: {path}")

    mock_sftp.open.side_effect = _open
    mock_sftp.rename.side_effect = _rename
    mock_sftp.posix_rename.side_effect = _rename
    mock_sftp.stat.side_effect = _stat


def test_ssl_config_no_change():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": RSA_CERT,
        "key_content": RSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": RSA_CERT,
                "/tmp/key.key": RSA_KEY,
            },
        )

        run_module()

        assert mock_module.exit_json.called
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert not mock_ssh.exec_command.called


def test_ssl_config_with_change():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": RSA_CERT,
        "key_content": RSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": "OLD_CERT",
                "/tmp/key.key": "OLD_KEY",
            },
        )

        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(channel=mock_channel), MagicMock())

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        mock_ssh.exec_command.assert_called_with("systemctl restart unifi-core", timeout=30)


def test_ssl_config_check_mode():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": RSA_CERT,
        "key_content": RSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": "OLD_CERT",
                "/tmp/key.key": "OLD_KEY",
            },
        )

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        assert not mock_ssh.exec_command.called


def test_ssl_config_cert_key_mismatch_fails():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "cert_content": RSA_CERT,
        "key_content": OTHER_RSA_KEY,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_module.fail_json.called
        msg = mock_module.fail_json.call_args[1]["msg"]
        assert "Certificate and private key do not match" in msg
        # Must fail BEFORE opening SSH connection
        assert not mock_ssh_cls.called


def test_ssl_config_expired_cert_fails():
    params = {
        "host": "192.0.2.1",
        "cert_content": EXPIRED_CERT,
        "key_content": None,
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
    ) as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_module.fail_json.called
        msg = mock_module.fail_json.call_args[1]["msg"]
        assert "expired" in msg


def test_ssl_config_future_cert_fails():
    params = {
        "host": "192.0.2.1",
        "cert_content": FUTURE_CERT,
        "key_content": None,
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
    ) as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_module.fail_json.called
        msg = mock_module.fail_json.call_args[1]["msg"]
        assert "not yet valid" in msg


def test_ssl_config_near_expiry_warns():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "cert_content": NEAR_CERT,
        "key_content": NEAR_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value
        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": NEAR_CERT,
                "/tmp/key.key": NEAR_KEY,
            },
        )

        run_module()

        assert mock_module.warn.called
        warn_text = mock_module.warn.call_args[0][0]
        assert "expires soon" in warn_text


def test_ssl_config_broken_chain_fails():
    broken_chain = f"{RSA_CERT}\n{FUTURE_CERT}"
    params = {
        "host": "192.0.2.1",
        "cert_content": broken_chain,
        "key_content": None,
    }

    with patch(
        "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
    ) as mock_module_class:
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json")

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_module.fail_json.called
        msg = mock_module.fail_json.call_args[1]["msg"]
        assert "Invalid certificate chain" in msg


def test_ssl_config_ecdsa_pairing_success():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "cert_content": ECDSA_CERT,
        "key_content": ECDSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": ECDSA_CERT,
                "/tmp/key.key": ECDSA_KEY,
            },
        )

        run_module()

        assert mock_module.exit_json.called
        assert mock_module.exit_json.call_args[1]["changed"] is False


def test_ssl_config_ed25519_pairing_success():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "cert_content": ED25519_CERT,
        "key_content": ED25519_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": ED25519_CERT,
                "/tmp/key.key": ED25519_KEY,
            },
        )

        run_module()

        assert mock_module.exit_json.called
        assert mock_module.exit_json.call_args[1]["changed"] is False


def test_ssl_config_service_restart_partial_failure():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "cert_content": RSA_CERT,
        "key_content": RSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        setup_mock_sftp(
            mock_sftp,
            {
                "/tmp/cert.crt": "OLD_CERT",
                "/tmp/key.key": "OLD_KEY",
            },
        )

        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = (
            b"Job for unifi-core.service failed because the control process exited with error code."
        )
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(channel=mock_channel), mock_stderr)

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_module.fail_json.called
        call_kwargs = mock_module.fail_json.call_args[1]
        assert call_kwargs.get("changed") is True
        assert "exit code 1" in call_kwargs["msg"]


def test_ssl_config_host_key_policies():
    for policy_val, policy_cls in [
        ("reject", paramiko.RejectPolicy),
        ("auto_add", paramiko.AutoAddPolicy),
        ("warning", paramiko.WarningPolicy),
    ]:
        params = {
            "host": "192.0.2.1",
            "ssh_username": "root",
            "cert_content": RSA_CERT,
            "host_key_policy": policy_val,
            "restart_service": False,
        }

        with (
            patch(
                "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
            ) as mock_module_class,
            patch(
                "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
            ) as mock_ssh_cls,
        ):
            mock_module = mock_module_class.return_value
            mock_module.params = params
            mock_module.check_mode = False

            mock_ssh = mock_ssh_cls.return_value
            mock_sftp = mock_ssh.open_sftp.return_value
            setup_mock_sftp(mock_sftp, {"/data/unifi-core/config/unifi-core.crt": RSA_CERT})

            run_module()

            mock_ssh.set_missing_host_key_policy.assert_called_once()
            called_policy = mock_ssh.set_missing_host_key_policy.call_args[0][0]
            assert isinstance(called_policy, policy_cls)


def test_ssl_config_finally_closes_handles():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "cert_content": RSA_CERT,
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_ssh_cls.return_value
        mock_sftp = mock_ssh.open_sftp.return_value
        # Cause exception during SFTP
        mock_sftp.open.side_effect = [OSError("File not found"), OSError("Write error")]

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        assert mock_sftp.close.called
        assert mock_ssh.close.called


def test_ssl_config_ssh_failure_never_leaks_password_or_key():
    fake_password = "super_secret_ssh_password_12345"
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": fake_password,
        "ssh_key": None,
        "cert_content": RSA_CERT,
        "key_content": RSA_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko.SSHClient"
        ) as mock_ssh_cls,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json called")

        mock_ssh = mock_ssh_cls.return_value
        mock_ssh.connect.side_effect = Exception(f"Connection failed for password: {fake_password} with {RSA_KEY}")

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        assert mock_module.fail_json.called
        fail_msg = mock_module.fail_json.call_args[1]["msg"]
        assert fake_password not in fail_msg
        assert "super_secret_ssh_password" not in fail_msg
        assert RSA_KEY not in fail_msg
        assert "PRIVATE KEY REDACTED" in fail_msg or "********" in fail_msg
