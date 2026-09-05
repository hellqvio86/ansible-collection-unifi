from unittest.mock import MagicMock

import pytest

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_ssl import (
    atomic_sftp_replace,
    check_cert_dates,
    sanitize_ssh_error,
    validate_cert_chain,
    validate_pem_cert,
    validate_pem_key,
    verify_cert_key_pair,
)

RSA_CERT = """-----BEGIN CERTIFICATE-----
MIICrjCCAZagAwIBAgIBajANBgkqhkiG9w0BAQsFADAaMRgwFgYDVQQDDA9FeGFt
cGxlIFJvb3QgQ0EwHhcNMjYwOTA0MTMzMTQxWhcNMjYxMjA0MTMzMTQxWjAbMRkw
FwYDVQQDDBBsZWFmLmV4YW1wbGUuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEAlIxZon3kx/SmyEbpDL6sjgmYibVpUIrP4eUWh1Mf2FXrbxTjlrMn
Q2OqYaFaSZPHrgQuKPhTCtyi55bXJPcfdXxHOsRKXF0xPCB+nvd+y8hRw37cHNjr
1WOoIUYcCae9H6za2KE4HdqwLXnm/Vss23Kxits/VJvJ9uelI9Y5Dc4hNl7JBYEE
3EZCY+C6iLVNI7J4/L5/0MO2uu2/br9M6FbCK1y/tsbtwXPpNHTtI1OkliijtE3x
fzF5laGYlIrAp2rro8aTSA+JSqITGiXdSOyKPyKtuHBbAvIevYFsTVAC4aqlqdGt
xmdy2ycwCfDbN93i9NiKYozFqJRzhElpVwIDAQABMA0GCSqGSIb3DQEBCwUAA4IB
AQBIPfGiyh2W79KAEsjSJ8YHg6ZZ5z+sQoWG5Mt+m1kiKU/NUKSTOp+24ouk17iN
YVYcGWGzHavETwdsBdJJEvmx31IsBF6hp4AidQwQyozuitwpYSm7KBe5D4DqyO+3
rf+JsPvKRi8Lj6wYFJRR16UJCYwjjKc0wg+Spzg8CyVh1IQganRZos2bkYUWjefA
Bb9Q8qEqK7HOPxfWGtMT/4hlLWFBvuqq9vgapH5jjSd1EvKcnLM/OOl9tTUbsYk9
jPOPQBfMpk31jUCwawrNX0A3neOPOslW5hCnnRtPJwz6bvrb7nc+jqqsX3F0BLzN
kiHF3jzaQVP5a3ImSb+iYLk8
-----END CERTIFICATE-----"""

RSA_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCUjFmifeTH9KbI
RukMvqyOCZiJtWlQis/h5RaHUx/YVetvFOOWsydDY6phoVpJk8euBC4o+FMK3KLn
ltck9x91fEc6xEpcXTE8IH6e937LyFHDftwc2OvVY6ghRhwJp70frNrYoTgd2rAt
eeb9WyzbcrGK2z9Um8n256Uj1jkNziE2XskFgQTcRkJj4LqItU0jsnj8vn/Qw7a6
7b9uv0zoVsIrXL+2xu3Bc+k0dO0jU6SWKKO0TfF/MXmVoZiUisCnauujxpNID4lK
ohMaJd1I7Io/Iq24cFsC8h69gWxNUALhqqWp0a3GZ3LbJzAJ8Ns33eL02IpijMWo
lHOESWlXAgMBAAECggEAEBeKKD+iFoUqwhxoZ6CKOdLRSu2zjG2VKn/yKlO3aeyY
1g45v1wF/1dfIDdl+/19zpyWUYrhGBahsRvWj6MTrdr6LmQQOCRCTqSogtkFy9aW
AOsPtjJLjfC/SGd7ZxJcOv+zL297kERd/Hctrjl/yQAKOqQYnrZHsS8T5SdyQ8vr
7TDdYjtEJK+WnaYf9twpxbz3MgW8dB0+tdechbwglT1zT1oVdP1tUwL4WZYP/jEV
hnmrmpddbCL1yy2JQff/8YgwqBe4xrNTAAZD1Z03zHpB0lQ2v6U+kUu7KffIKIJg
xOaCpsuHtEGwcDrjBfHUrLH0YAX1awQzVpb7fKWrpQKBgQDFbyUBgrdvuklN9s9O
WgHviC6dglLS0xZ5TXt7ym1Tt9CIwX2S+SOeutQQMugQfb/FU7BKRY8h477KlsiV
FPV3TGRg4RiHrIKKMpNMa2e5L6kteVBWOEGxNlVYQtKmubJ7JSbnyG86C2TJxHt2
52FUwCz3Jb4KlkqSIpQRck7/vQKBgQDAnOHPnuPR5Mmvq9Z/kIq0WcVqLoBIxUqg
ED2WS1uJGvW8C0HSGqfuUXQ4r66FH2r0mreYANtnuLbIhSxUfIbiWixhB7gOcOhT
jKBjDmexaAgf+XBLf4iRgx0Xn1/jcN8OpACl1g4389xuWf+/z91oe9CvvFdCsm+o
odhtVX4kowKBgGruSoWp7X320BMI1Lij6R55jH3EguUqbKagP3wJY/MOwEQBP+jl
RNSIbaikWans4XuXWwiu6dm6BrCkv9h2tIe7eTY7U9TPqxf8Umj2VwQmeyNk7Az2
hSXcvpaCAqNIOhGWSp8IoK04VIsu/oukv8NuHixxZZ9ITPUfA0D7vyulAoGAdXl5
k+qhomt6wyT4Dxd2MWcrK4avATMrP5KILXlKm8WQqJ7pBx7w2z5ctxIXS+QMlKEk
ZpXnO0yCVqw6jFDi53z94jQWAuDEIej8DU5E2gPMKMw2vCVNgwpHnRe8IPi/YquO
JZb3VxLpl3hWroM107roXbZuNiSkS2JioNRquicCgYEAu2cIZbGH0LqIVR4KzJaf
d0WfgF8EYTXnjed643+Dz7XLTtpKxAgApXHbo1+I2N7otlWbkyaWQb+WbNTKWrDa
RW7mLWnFPOIEVfBGFFg9ndrlpUR7eifxFokvg5Gz7J/t6GKfHUwjI2g5YjQMBvbd
3lfvhV0N4g6pRmnVTT2PGws=
-----END PRIVATE KEY-----"""

CA_CERT = """-----BEGIN CERTIFICATE-----
MIICrTCCAZWgAwIBAgIBaTANBgkqhkiG9w0BAQsFADAaMRgwFgYDVQQDDA9FeGFt
cGxlIFJvb3QgQ0EwHhcNMjYwODA2MTMzMTQxWhcNMjcwOTA1MTMzMTQxWjAaMRgw
FgYDVQQDDA9FeGFtcGxlIFJvb3QgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
ggEKAoIBAQDNWMND0AyqG92Da/38hRP5NWZUwQB8idlh+r0RVyb3ShvBT/eCbmJI
Nlhfqs08bHIn6IwrTk2ZaoiIXd6ie9srnXedifEP7+9vWy6Mymth2Ap+ueTdXHpn
RXQ10Q+wvRRhuZP4CgCpzwLCWZ6T6ErpF/xJ3Y4lsuoD2JJ8vnhtuCW25m3ubl6p
O1SjB3ywoJQL4ny1MzeVPyuUXQeijDGx5MT90zmtF362Pf2AgrUZvXlkef+RtAut
P6bbpy3C8RT4j8zQMbliQr72551MH+Uf045VqobxAo5uRvpneYEZnH0Fns0qls6w
H/IJj+K7bmZzOiv2/oUZeGacsu+9VWFRAgMBAAEwDQYJKoZIhvcNAQELBQADggEB
AIF6BhSbnPDQi4nIZhy2BAnlT9XBtJSSqGZz4q3Vb037IBpjmjEB5pcuUA+DORFa
f3BCC+bwOCK8WrCmty4W07KBzoejXy+W6QrAokpL3OuEk8bfH7VqN6DY4htSR5u/
mQo4TbsGVSxYmvsetMKlpuyTYwprCJSd85V/buGp57XKfkvnjy+kRV78F6fCwf8o
n586Km/Tov3a4aS1IqWq51xzOv+JK4DPAE06FhcgGVXbNTmRP78RMUC1RmMuOlgj
NQfbiVzrsV9L1jVcRL/ATWxLE1kQnIdJerKkLMHD2DVecKcVrrRYoktFcx4Yl4Zc
a5Bdf9VzWNrHC8zJJck98yk=
-----END CERTIFICATE-----"""

ECDSA_CERT = """-----BEGIN CERTIFICATE-----
MIIBqDCCAU6gAwIBAgIBZDANBgkqhkiG9w0BAQsFADAaMRgwFgYDVQQDDA9lY2Rz
YS5leGFtcGxlLmNvbTAeFw0yNjA5MDQxMzMxNDFaFw0yNjEyMDQxMzMxNDFaMBox
GDAWBgNVBAMMD2VjZHNhLmV4YW1wbGUuY29tMFkwEwYHKoZIzj0CAQYIKoZIzj0D
AQcDQgAE/c1jQjF5b/bB4G7f9lA0eA13q+QpX/cE59V83w2G2k9A8qX8f+6q8/vT
K7n6pG+QWz4eLzY3x8c1bE1a4a+XrqOBkzCBkDAOBgNVHQ8BAf8EBAMCAqQwHQYD
VR0OBBYEFPv61lO+s7yVb6P9B6K8Z6K1p2vSMB8GA1UdIwQYMBaAFPv61lO+s7yV
b6P9B6K8Z6K1p2vSMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAJyK
+7M6k3t6s4sM9K9Yw+wQ5j7K3f+l9/4v1a0b3sXqY6j6e8sX8e0a1b8c2d3e4f5g
6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m
-----END CERTIFICATE-----"""

ECDSA_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg9R8k0w4Z7B9dY7G+
e7s2l0Y6E2f1Q9q8T7A4k0M1X4WhRANCAAT9zWNCKXlv9sHgbt/2UDR4DXer5Clf
9wTn1XzfDYbaT0Dypfx/7qrz+9Mrufakb5BbPh4vNjfHxzVsTVrhr5eu
-----END PRIVATE KEY-----"""

ED25519_CERT = """-----BEGIN CERTIFICATE-----
MIIBTzCB+qADAgECAgFlMAUGAytlcDAaMRgwFgYDVQQDDA9lZDI1NTE5LmV4YW1w
bGUuY29tMB4XDTI2MDkwNDEzMzE0MVoXDTI2MTIwNDEzMzE0MVowGjEYMBYGA1UE
AwwPZWQyNTUxOS5leGFtcGxlLmNvbTAqMAUGAytlcAMhAC7Y3W7+8j+2sV6z5o0A
4tZ7U+q+0v8w9c2a3K5n7A6oo0EwPzAOBgNVHQ8BAf8EBAMCAqQwHQYDVR0OBBYE
FO0w2e+7g4b8u/2q6h3r+u5w6j8LMAwGA1UdEwQFMAMBAf8wBQYDK2VwA0EAP/1l
3s5e6o7b8d9c0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z
-----END CERTIFICATE-----"""

ED25519_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIPm4d2K8y8E9R+z4V6q8s+t1K3A4D6F8G0J2L4N6P8R0
-----END PRIVATE KEY-----"""

EXPIRED_CERT = """-----BEGIN CERTIFICATE-----
MIICszCCAZugAwIBAgIBajANBgkqhkiG9w0BAQsFADAeMRwwGgYDVQQDDBNleHBp
cmVkLmV4YW1wbGUuY29tMB4XDTI2MDcwNjEzMzE0MVoXDTI2MDgyNjEzMzE0MVow
HjEcMBoGA1UEAwwTZXhwaXJlZC5leGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEB
BQADggEPADCCAQoCggEBALyD8XyZl4+q9j5w0K7u8p6a3c4f5v7e2a9b3d5c7f1a
2b4d6f8h0j2l4n6p8r0t2v4x6z8b0d2f4h6j8l0n2p4r6t8v0x2z4b6d8f0h2j4l
6n8p0r2t4v6x8z0b2d4f6h8j0l2n4p6r8t0v2x4z6b8d0f2h4j6l8n0p2r4t6v8x
0z2b4d6f8h0j2l4n6p8r0t2v4x6z8b0d2f4h6j8l0n2p4r6t8v0x2z4b6d8f0h2j
4l6n8p0r2t4v6x8z0b2d4f6h8j0l2n4p6r8t0v2x4z6b8d0f2h4j6l8n0p2r4t6v
8wIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQC0+r5v8s9t0u1v2w3x4y5z6a7b8c9d
-----END CERTIFICATE-----"""

FUTURE_CERT = """-----BEGIN CERTIFICATE-----
MIICszCCAZugAwIBAgIBZzANBgkqhkiG9w0BAQsFADAdMRswGQYDVQQDDBJmdXR1
cmUuZXhhbXBsZS5jb20wHhcNMjYwOTE1MTMzMTQxWhcNMjYxMjA0MTMzMTQxWjAd
MRswGQYDVQQDDBJmdXR1cmUuZXhhbXBsZS5jb20wggEiMA0GCSqGSIb3DQEBAQUA
A4IBDwAwggEKAoIBAQC2NirphX2xywaTQjtxG12CwuMge0rpnTEmucb4iCWFLP+8
2a1PdV2cNN1qBSqlSyLgzsAKeRuWu374GFD4BLuFY5PMqoKQT1/kpbm11FkF/N9e
dTpyPFqPYzOyn/+pbldLqDWVIwgTVBQTvp4aq9NAsiQdtgpVG1YQkH89AojjDzzH
y6peytkuObqxQmjUPG4pLUmwCv8nMGXecZWIUIJrsBE45u1/hUw4q2hClXQuaBMx
XEFRr8scf+1C0ZE99z7hvVgJ1SLcvXF9J1YMdKZNXN86eH9dA6UbrfGV1sf+DfVi
6Q5YMTM8a8igIwENKtnJu3JFJlWLfpldkO9KQXUPAgMBAAEwDQYJKoZIhvcNAQEL
BQADggEBAAzZTno3b1YMNg2+Ar+VNQurORik8aw6RhCMgTM9k/t8xTv/7fsg/yb6
Bt8DhUL45IgKzxsxe6BULyF9bodwdwl+0f1Uy8USRSe/8Gpd4XiSOEhG+yvVzFZ2
gN4whLjU6dJPAOladD1f7GULkfBn1hQwS/4EqgqaECLKuoQjbADCKYowowgNQ/RM
xAkdXGg2ahpZwERJnWRCcI//sipa01TQht6y8BHeGqI4wmBsb74/UVf4MxWEJwoc
x0i9BhlH/rLIcfIj6agLl32zwtcLk6wPobUVSaKijK9HXq9AmKJBI6GcPONwa7xq
m+mGqlZpDSUtJK5VxmL8O4MZQ1Dse+A=
-----END CERTIFICATE-----"""


def test_validate_pem_cert_success():
    valid, err, certs = validate_pem_cert(RSA_CERT)
    assert valid is True
    assert err == ""
    assert len(certs) == 1


def test_validate_pem_cert_invalid():
    valid, err, certs = validate_pem_cert("not-a-cert")
    assert valid is False
    assert "missing BEGIN or END CERTIFICATE" in err

    valid, err, certs = validate_pem_cert("")
    assert valid is False
    assert "empty" in err


def test_validate_pem_key_success():
    valid, err, key = validate_pem_key(RSA_KEY)
    assert valid is True
    assert err == ""
    assert key is not None


def test_validate_pem_key_invalid():
    valid, err, key = validate_pem_key("not-a-key")
    assert valid is False
    assert "missing BEGIN or END KEY" in err

    valid, err, key = validate_pem_key("")
    assert valid is False
    assert "empty" in err


def test_verify_cert_key_pair_matching_rsa():
    _, _, certs = validate_pem_cert(RSA_CERT)
    _, _, key = validate_pem_key(RSA_KEY)
    matched, err = verify_cert_key_pair(certs[0], key)
    assert matched is True
    assert err == ""


def test_verify_cert_key_pair_mismatch():
    _, _, certs = validate_pem_cert(RSA_CERT)
    # Validate against another key (e.g. ECDSA_KEY)
    from cryptography.hazmat.primitives.asymmetric import rsa

    other_key = rsa.generate_private_key(65537, 2048)
    matched, err = verify_cert_key_pair(certs[0], other_key)
    assert matched is False
    assert "does not match" in err


def test_validate_cert_chain_valid():
    chain_pem = f"{RSA_CERT}\n{CA_CERT}"
    _, _, certs = validate_pem_cert(chain_pem)
    assert len(certs) == 2
    valid, err = validate_cert_chain(certs)
    assert valid is True
    assert err == ""


def test_validate_cert_chain_broken():
    broken_chain_pem = f"{RSA_CERT}\n{FUTURE_CERT}"
    _, _, certs = validate_pem_cert(broken_chain_pem)
    assert len(certs) == 2
    valid, err = validate_cert_chain(certs)
    assert valid is False
    assert "chain broken" in err


def test_check_cert_dates_valid():
    _, _, certs = validate_pem_cert(RSA_CERT)
    valid, err, warnings = check_cert_dates(certs, warning_days=10)
    assert valid is True
    assert err == ""


def test_check_cert_dates_future():
    _, _, certs = validate_pem_cert(FUTURE_CERT)
    valid, err, warnings = check_cert_dates(certs)
    assert valid is False
    assert "not yet valid" in err


def test_sanitize_ssh_error_redaction():
    fake_secret = "secret_password_123"
    fake_key_path = "/root/.ssh/id_ed25519"
    err = Exception(f"Failed to load key {fake_key_path} with password={fake_secret}\n{RSA_KEY}")

    sanitized = sanitize_ssh_error(err, secrets=[fake_secret])
    assert fake_secret not in sanitized
    assert fake_key_path not in sanitized
    assert "PRIVATE KEY REDACTED" in sanitized
    assert "********" in sanitized


def test_atomic_sftp_replace_posix_rename():
    sftp = MagicMock()
    # posix_rename succeeds
    atomic_sftp_replace(sftp, "/remote/path.crt", "test_content", mode=0o644)
    assert sftp.open.called
    assert sftp.chmod.called
    assert sftp.posix_rename.called


def test_atomic_sftp_replace_fallback_with_backup():
    sftp = MagicMock()
    # posix_rename fails
    sftp.posix_rename.side_effect = OSError("posix rename not supported")
    # stat succeeds (file existed)
    sftp.stat.return_value = MagicMock(st_mode=0o100644)

    atomic_sftp_replace(sftp, "/remote/path.crt", "test_content", mode=0o644)
    # Should have backed up, renamed tmp, removed backup
    assert sftp.rename.call_count >= 2


def test_atomic_sftp_replace_rollback_on_rename_failure():
    sftp = MagicMock()
    sftp.posix_rename.side_effect = OSError("posix rename not supported")
    sftp.stat.return_value = MagicMock(st_mode=0o100644)
    # First rename (backup) succeeds, second rename (tmp to target) fails
    sftp.rename.side_effect = [None, OSError("disk full"), None]

    with pytest.raises(OSError, match="restored previous file from backup"):
        atomic_sftp_replace(sftp, "/remote/path.crt", "test_content", mode=0o644)
