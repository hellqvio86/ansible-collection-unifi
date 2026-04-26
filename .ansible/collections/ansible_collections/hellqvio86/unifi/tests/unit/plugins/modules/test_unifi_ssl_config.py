from unittest.mock import MagicMock, patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssl_config import run_module


def test_ssl_config_no_change():
    params = {
        "host": "192.168.1.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": "CERT_CONTENT",
        "key_content": "KEY_CONTENT",
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

        # Configure Mock SSH and SFTP
        mock_ssh = mock_paramiko.SSHClient.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        # Mock reading current cert/key (same as desired)
        mock_file_cert = MagicMock()
        mock_file_cert.__enter__.return_value = mock_file_cert
        mock_file_cert.read.return_value = b"CERT_CONTENT"
        mock_file_key = MagicMock()
        mock_file_key.__enter__.return_value = mock_file_key
        mock_file_key.read.return_value = b"KEY_CONTENT"

        mock_sftp.open.side_effect = [mock_file_cert, mock_file_key]

        run_module()

        assert mock_module.exit_json.called
        args, kwargs = mock_module.exit_json.call_args
        assert kwargs["changed"] is False


def test_ssl_config_with_change():
    params = {
        "host": "192.168.1.1",
        "ssh_username": "root",
        "ssh_password": "password",
        "ssh_key": None,
        "cert_content": "NEW_CERT",
        "key_content": "NEW_KEY",
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

        mock_ssh = mock_paramiko.SSHClient.return_value
        mock_sftp = mock_ssh.open_sftp.return_value

        # Mock reading current (different)
        mock_file_cert = MagicMock()
        mock_file_cert.__enter__.return_value = mock_file_cert
        mock_file_cert.read.return_value = b"OLD_CERT"
        mock_file_key = MagicMock()
        mock_file_key.__enter__.return_value = mock_file_key
        mock_file_key.read.return_value = b"OLD_KEY"

        # SFTP open will be called for reading and then for writing
        # read cert, write cert, read key, write key
        mock_sftp.open.side_effect = [
            mock_file_cert,  # read cert
            MagicMock(),  # write cert
            mock_file_key,  # read key
            MagicMock(),  # write key
        ]

        run_module()

        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
        # Verify restart command was sent
        mock_ssh.exec_command.assert_called_with("systemctl restart unifi-core")
