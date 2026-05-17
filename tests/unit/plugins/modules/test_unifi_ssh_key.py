from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key import run_module


def test_ssh_key_present_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "validate_certs": False,
        "keys": ["ssh-rsa AAAA..."],
        "state": "present",
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        # Mock responses: user already has the key
        mock_api.request.side_effect = [({"sshKeys": ["ssh-rsa AAAA..."]}, {"status": 200})]

        run_module()

        # Should not call PATCH
        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once_with(changed=False, keys_count=1)


def test_ssh_key_present_with_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "validate_certs": False,
        "keys": ["ssh-rsa NEW..."],
        "state": "present",
    }

    with (
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key.AnsibleModule") as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_ssh_key.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        # Mock responses: user has old key, needs new key
        mock_api.request.side_effect = [
            ({"sshKeys": ["ssh-rsa OLD..."]}, {"status": 200}),
            ({"sshKeys": ["ssh-rsa OLD...", "ssh-rsa NEW..."]}, {"status": 200}),
        ]

        run_module()

        # Should call PATCH
        assert mock_api.request.call_count == 2
        last_call = mock_api.request.call_args_list[1]
        assert last_call[1]["method"] == "PATCH"
        assert "ssh-rsa NEW..." in last_call[1]["data"]["sshKeys"]

        mock_module.exit_json.assert_called_once_with(changed=True, keys_count=2)
