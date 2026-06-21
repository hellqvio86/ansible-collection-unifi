from unittest.mock import patch

from ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate import run_module

TEST_CERT = """-----BEGIN CERTIFICATE-----
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

TEST_KEY = """-----BEGIN PRIVATE KEY-----
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


def test_cert_create():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": TEST_CERT,
        "key": TEST_KEY,
        "active": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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

        mock_api.request.side_effect = [
            ([], {"status": 200}),
            ({"id": "cert1", "name": "mycert"}, {"status": 201}),
            ({"id": "cert1", "name": "mycert", "active": True}, {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 3
        post_call = mock_api.request.call_args_list[1]
        assert post_call[1]["method"] == "POST"
        assert post_call[1]["data"]["name"] == "mycert-8fcabe9d"
        status_call = mock_api.request.call_args_list[2]
        assert status_call[1]["method"] == "PUT"
        assert status_call[1]["data"]["active"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_no_change():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": TEST_CERT,
        "key": TEST_KEY,
        "active": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert", "active": True, "fingerprint": "8F:CA:BE:9D:1E:82:41:04:27:6C:67:AE:EB:A2:B9:52:0D:34:E5:9C"}], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_cert_activate_existing():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": TEST_CERT,
        "key": TEST_KEY,
        "active": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert", "active": False, "fingerprint": "8F:CA:BE:9D:1E:82:41:04:27:6C:67:AE:EB:A2:B9:52:0D:34:E5:9C"}], {"status": 200}),
            ({"id": "cert1", "name": "mycert", "active": True}, {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        status_call = mock_api.request.call_args_list[1]
        assert status_call[1]["method"] == "PUT"
        assert status_call[1]["data"]["active"] is True

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_absent():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "mycert",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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

        mock_api.request.side_effect = [
            ([{"id": "cert1", "name": "mycert"}], {"status": 200}),
            ({}, {"status": 204}),
        ]

        run_module()

        assert mock_api.request.call_count == 2
        delete_call = mock_api.request.call_args_list[1]
        assert delete_call[1]["method"] == "DELETE"

        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True


def test_cert_absent_noop():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "absent",
        "name": "NonExistent",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
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

        mock_api.request.side_effect = [
            ([], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is False


def test_cert_missing_params():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": None,
        "key": None,
        "active": False,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as _,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = Exception("fail_json")

        import pytest

        with pytest.raises(Exception, match="fail_json"):
            run_module()

        mock_module.fail_json.assert_called_once()
        args = mock_module.fail_json.call_args[1]
        assert "cert" in args["msg"].lower() and "key" in args["msg"].lower()


def test_cert_check_mode():
    params = {
        "host": "192.0.2.1",
        "username": "admin",
        "password": "password",
        "site": "default",
        "validate_certs": False,
        "state": "present",
        "name": "mycert",
        "cert": TEST_CERT,
        "key": TEST_KEY,
        "active": True,
    }

    with (
        patch(
            "ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.AnsibleModule"
        ) as mock_module_class,
        patch("ansible_collections.hellqvio86.unifi.plugins.modules.unifi_user_certificate.UnifiAPI") as mock_api_class,
    ):
        mock_module = mock_module_class.return_value
        mock_module.params = params
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = Exception("fail_json")

        mock_api = mock_api_class.return_value
        mock_api.as_list.side_effect = lambda x: (
            x
            if isinstance(x, list)
            else (x.get("data", []) if isinstance(x, dict) and isinstance(x.get("data"), list) else [])
        )

        mock_api.request.side_effect = [
            ([], {"status": 200}),
        ]

        run_module()

        assert mock_api.request.call_count == 1
        mock_module.exit_json.assert_called_once()
        kwargs = mock_module.exit_json.call_args[1]
        assert kwargs["changed"] is True
