import base64
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from http.cookies import SimpleCookie
from typing import Any

from ansible.module_utils.urls import fetch_url

try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import jwt

    HAS_JWT = True
except ImportError:
    HAS_JWT = False


@contextmanager
def _host_lock(host: str | None):
    if not HAS_FCNTL or not host:
        yield
        return

    host_hash = hashlib.sha256(host.encode("utf-8")).hexdigest()[:12]
    lock_path = os.path.join(tempfile.gettempdir(), f"ansible_unifi_{host_hash}.lock")
    lock_fd = None
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
    except Exception:
        pass

    try:
        yield
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except Exception:
                pass


class UnifiAPI:
    def __init__(
        self,
        module: Any,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        validate_certs: bool | None = None,
        session_cookie: str | None = None,
        csrf_token: str | None = None,
        ca_path: str | None = None,
    ) -> None:
        self.module = module

        # Fallback to environment variables if not provided
        self.host = host or os.environ.get("UNIFI_HOST")
        self.username = username or os.environ.get("UNIFI_USERNAME")
        self.password = password or os.environ.get("UNIFI_PASSWORD")

        # Handle validate_certs fallback (defaults to True for security)
        if validate_certs is not None:
            self.validate_certs = validate_certs
        else:
            env_val = os.environ.get("UNIFI_VALIDATE_CERTS", "true").lower()
            self.validate_certs = env_val in ["true", "1", "yes", "on"]

        self.ca_path = ca_path or os.environ.get("UNIFI_CA_PATH")
        self.session_cookie = session_cookie
        self.csrf_token = csrf_token

        if not self.host:
            self.module.fail_json(
                msg="UniFi host not provided. Set 'host' parameter or 'UNIFI_HOST' environment variable."
            )

        self.base_url = f"https://{self.host}"

        # Ensure the module has the validate_certs and ca_path parameters set as expected by fetch_url
        if hasattr(self.module, "params"):
            self.module.params["validate_certs"] = self.validate_certs
            if self.ca_path:
                self.module.params["ca_path"] = self.ca_path

    def _fetch_with_retry(self, url: str, method: str, headers: dict[str, str], payload: str | None):
        retries = 5
        backoff = 2

        for attempt in range(retries + 1):
            response, info = fetch_url(
                self.module,
                url,
                data=payload,
                method=method,
                headers=headers,
                timeout=30,
                ca_path=self.ca_path,
            )
            if info.get("status") != 429:
                return response, info
            if attempt < retries:
                time.sleep(backoff)
                backoff *= 2
        return response, info

    def login(self) -> bool:
        if self.session_cookie and self.csrf_token:
            return True
        if not self.username or not self.password:
            self.module.fail_json(
                msg="UniFi credentials not provided. Set 'username'/'password' or 'UNIFI_USERNAME'/'UNIFI_PASSWORD' environment variables."
            )

        login_url = f"{self.base_url}/api/auth/login"
        login_payload = json.dumps({"username": self.username, "password": self.password})

        with _host_lock(self.host):
            response, info = self._fetch_with_retry(
                login_url,
                "POST",
                {"Content-Type": "application/json"},
                login_payload,
            )

            if info.get("status") != 200:
                status = info.get("status")
                if status == 429:
                    self.module.fail_json(
                        msg=(
                            "UniFi login rate limit reached. Wait a few minutes before retrying; "
                            "the module stops after this single login attempt."
                        ),
                        info=info,
                    )
                if status in [401, 403]:
                    self.module.fail_json(
                        msg="UniFi login failed: invalid credentials or account not permitted for local API login.",
                        info=info,
                    )
                self.module.fail_json(msg=f"Login failed: {info.get('msg', 'Unknown error')}", info=info)

            # Extract Cookies and construct clean RFC 6265 Request Cookie header
            set_cookie_raw = info.get("set-cookie") or info.get("Set-Cookie") or ""
            cookie_list = set_cookie_raw if isinstance(set_cookie_raw, list) else [str(set_cookie_raw)]
            raw_cookie_str = "; ".join(cookie_list)

            cookie_jar = SimpleCookie()
            for item in cookie_list:
                if item:
                    try:
                        cookie_jar.load(item)
                    except Exception:
                        pass

            if cookie_jar:
                self.session_cookie = "; ".join(f"{k}={v.value}" for k, v in cookie_jar.items())
            else:
                self.session_cookie = raw_cookie_str

            # Extract CSRF Token from JWT in TOKEN cookie
            token_val = None
            if "TOKEN" in cookie_jar:
                token_val = cookie_jar["TOKEN"].value

            if not token_val:
                m = re.search(r"(?:^|;\s*|\b)TOKEN=([^;]+)", raw_cookie_str)
                if m:
                    token_val = m.group(1)

            if token_val:
                decoded = False
                if HAS_JWT:
                    try:
                        payload = jwt.decode(token_val, options={"verify_signature": False})
                        self.csrf_token = payload.get("csrfToken")
                        decoded = True
                    except Exception:
                        pass

                if not decoded:
                    try:
                        parts = token_val.split(".")
                        if len(parts) >= 2:
                            payload_b64 = parts[1]
                            padding = "=" * ((4 - len(payload_b64) % 4) % 4)
                            payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
                            payload = json.loads(payload_bytes.decode("utf-8"))
                            self.csrf_token = payload.get("csrfToken")
                            decoded = True
                    except Exception as e:
                        self.module.fail_json(msg=f"Failed to decode JWT for CSRF: {str(e)}")

        return True

    def request(
        self, path: str, method: str = "GET", data: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any] | bytes | None, dict[str, Any]]:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json", "Cookie": self.session_cookie, "X-CSRF-Token": self.csrf_token}

        payload = json.dumps(data) if data else None
        response, info = self._fetch_with_retry(url, method, headers, payload)

        if info.get("status") in [401, 403] and self.username and self.password:
            self.session_cookie = None
            self.csrf_token = None
            self.login()
            headers = {
                "Content-Type": "application/json",
                "Cookie": self.session_cookie,
                "X-CSRF-Token": self.csrf_token,
            }
            response, info = self._fetch_with_retry(url, method, headers, payload)

        if info.get("status") not in [200, 201, 204]:
            return None, info

        if response is None:
            return {}, info

        res_data = response.read()
        try:
            return json.loads(res_data) if res_data else {}, info
        except ValueError:
            return res_data, info

    def as_list(self, payload: dict[str, Any] | list[Any] | None) -> list[Any]:
        """Helper to extract a list from UniFi API responses which often wrap data in a 'data' key."""
        if payload is None:
            return []
        if isinstance(payload, dict):
            if isinstance(payload.get("data"), list):
                return payload["data"]
            return []
        if isinstance(payload, list):
            return payload
        return []
