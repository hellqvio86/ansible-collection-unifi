from unittest.mock import MagicMock, patch

import pytest

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config import run_module

VALID_CERT = """-----BEGIN CERTIFICATE-----
MIIBkjCB/KADAgECAgIwOTANBgkqhkiG9w0BAQsFADAPMQ0wCwYDVQQDDAR0ZXN0
MB4XDTI2MDEwMTAwMDAwMFoXDTI3MDEwMTAwMDAwMFowDzENMAsGA1UEAwwEdGVz
dDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA69VsgDxkbzlfifvYKvpjB2q7
+hN+Y/ptQiv8MysViWPDvM7pYabhqCuoqhrXJn9S/ldrxb3hciUCeK3kuUOTnXRa
xJCFjV7P8HbDbAw5pU9UQRwl4/+aLuLvs80DL9NfU8lNmP9GMwmZOzB4DKIKP4ew
BRVWTvA3aavZFGkHfjMCAwEAATANBgkqhkiG9w0BAQsFAAOBgQA5OQ5TA3qLdcye
Ezx81HqRgqFAZZHzrgGM+afYPLkGkmL3ZJVsc5IKv1tceElRVZzg8sXUNysG7ReK
PRMdMtiahVdtPuXskBjPzAB6hbjiIixJVUX052Z9MPUqZoli0ya2kRaSD0z2heNH
yY1NVWKl/hFQw1vrA07wq62GsGJ61g==
-----END CERTIFICATE-----"""

VALID_KEY = """-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAOvVbIA8ZG85X4n7
2Cr6Ywdqu/oTfmP6bUIr/DMrFYljw7zO6WGm4agrqKoa1yZ/Uv5Xa8W94XIlAnit
5LlDk510WsSQhY1ez/B2w2wMOaVPVEEcJeP/mi7i77PNAy/TX1PJTZj/RjMJmTsw
eAyiCj+HsAUVVk7wN2mr2RRpB34zAgMBAAECgYAul9f77fKZ1uf9RviKZTWzfW7u
FXPfJNb5P99v7I8wubkuUGLjnCjxJM8J7IudW4J2JadxRfaIqq82UITj5WoATKMV
aIT4NCbHsGvhoXaeXbK1KgjOlwTtDk80O9udoixIVBKK7/ww3vVYTAdBT/DZtLmd
7pJB25nE52L/RWi1IQJBAPtllkBKHdNIsyuUxqqgOyub2xXQqDPINqV9UOWEZKJo
W3KnRhI8ab8qrL5CWApr9HOjkiyjgs/I49RZD+ZzG58CQQDwJuKi6J5rrUhhpqhH
5DuhhjOh7zNqojNVAlnT9tDt3L5IW4dPR51BxImEA00qCsQgjrq3B2kTJxk8BRDr
IZTtAkAP1bZBFmoKhOnENPrOhIk1lfuWxC3UFShcBCi0TEKKeEhKUH75ZxTCFc4L
reIdxe7/2a27YhE7RUwUdAesXFPBAkEA3rAAKnYwKMLnQn3Kv9dYoEAUcs2fTPsZ
RHPIni/ZryepXulYwGA053560epJzHltQo93fi8l9TelQ62i8ZYTRQJAfI4Al5tb
IWjAoIwB/+24s0kMHktLiMKF1cJJVuwsR4U5BkA4mhjYiRa6UcZitro/PjzrN1/d
U0w6nGai7j6b5Q==
-----END PRIVATE KEY-----"""


def test_ssl_config_no_change():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": VALID_CERT,
        "key_content": VALID_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko") as mock_paramiko,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_paramiko.SSHClient.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        mock_file_cert = MagicMock()
        mock_file_cert.__enter__.return_value = mock_file_cert
        mock_file_cert.read.return_value = VALID_CERT.encode("utf-8")
        mock_file_key = MagicMock()
        mock_file_key.__enter__.return_value = mock_file_key
        mock_file_key.read.return_value = VALID_KEY.encode("utf-8")

        mock_sftp.open.side_effect = [mock_file_cert, mock_file_key]

        run_module()

        assert mock_module.exit_json.called
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_ssl_config_with_change():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": VALID_CERT,
        "key_content": VALID_KEY,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko") as mock_paramiko,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_paramiko.SSHClient.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        mock_file_cert = MagicMock()
        mock_file_cert.__enter__.return_value = mock_file_cert
        mock_file_cert.read.return_value = b"OLD_CERT"
        mock_file_key = MagicMock()
        mock_file_key.__enter__.return_value = mock_file_key
        mock_file_key.read.return_value = b"OLD_KEY"

        mock_sftp.open.side_effect = [
            mock_file_cert,
            MagicMock(),
            mock_file_key,
            MagicMock(),
        ]

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        mock_ssh.exec_command.assert_called_with("systemctl restart unifi-core")


def test_ssl_config_invalid_pem_cert_fails():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "cert_content": "not-a-pem-cert",
        "key_content": VALID_KEY,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko"),
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json called")

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "Invalid PEM certificate" in mock_module.fail_json.call_args[1]["msg"]


def test_ssl_config_invalid_pem_key_fails():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "cert_content": VALID_CERT,
        "key_content": "not-a-pem-key",
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko"),
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.fail_json.side_effect = Exception("fail_json called")

        with pytest.raises(Exception, match="fail_json called"):
            run_module()

        mock_module.fail_json.assert_called_once()
        assert "Invalid PEM private key" in mock_module.fail_json.call_args[1]["msg"]


def test_ssl_config_only_cert():
    params = {
        "host": "192.0.2.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": VALID_CERT,
        "key_content": None,
        "cert_path": "/tmp/cert.crt",
        "key_path": "/tmp/key.key",
        "restart_service": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config.paramiko") as mock_paramiko,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_ssh = mock_paramiko.SSHClient.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        mock_file_cert = MagicMock()
        mock_file_cert.__enter__.return_value = mock_file_cert
        mock_file_cert.read.return_value = b"OLD_CERT"

        mock_sftp.open.side_effect = [mock_file_cert, MagicMock()]

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        # Only cert was read/written (2 sftp opens, none for key)
        assert mock_sftp.open.call_count == 2
