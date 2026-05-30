import base64
import json
import os
import time

from ansible.module_utils.urls import fetch_url

try:
    import jwt  # noqa: F401

    HAS_JWT = True
except ImportError:
    HAS_JWT = False


from typing import Any


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
    ) -> None:
        self.module = module

        # Fallback to environment variables if not provided
        self.host = host or os.environ.get("UNIFI_HOST")
        self.username = username or os.environ.get("UNIFI_USERNAME")
        self.password = password or os.environ.get("UNIFI_PASSWORD")

        # Handle validate_certs fallback
        if validate_certs is not None:
            self.validate_certs = validate_certs
        else:
            env_val = os.environ.get("UNIFI_VALIDATE_CERTS", "false").lower()
            self.validate_certs = env_val in ["true", "1", "yes", "on"]

        self.session_cookie = session_cookie
        self.csrf_token = csrf_token

        if not self.host:
            self.module.fail_json(
                msg="UniFi host not provided. Set 'host' parameter or 'UNIFI_HOST' environment variable."
            )

        self.base_url = f"https://{self.host}"

        # Ensure the module has the validate_certs parameter set as expected by fetch_url
        if hasattr(self.module, "params"):
            self.module.params["validate_certs"] = self.validate_certs

    def _fetch_with_retry(self, url: str, method: str, headers: dict[str, str], payload: str | None):
        import fcntl
        import time
        
        retries = 5
        backoff = 2
        
        lock_file = "/tmp/ansible_unifi_api.lock"
        with open(lock_file, "w") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                for attempt in range(retries + 1):
                    response, info = fetch_url(self.module, url, data=payload, method=method, headers=headers)
                    if info.get("status") != 429:
                        return response, info
                    if attempt < retries:
                        time.sleep(backoff)
                        backoff *= 2
                return response, info
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

    def login(self) -> bool:
        if self.session_cookie and self.csrf_token:
            return True
        if not self.username or not self.password:
            self.module.fail_json(
                msg="UniFi credentials not provided. Set 'username'/'password' or 'UNIFI_USERNAME'/'UNIFI_PASSWORD' environment variables."
            )

        login_url = f"{self.base_url}/api/auth/login"
        login_payload = json.dumps({"username": self.username, "password": self.password})

        response, info = self._fetch_with_retry(
            login_url,
            "POST",
            {"Content-Type": "application/json"},
            login_payload,
        )

        if info["status"] != 200:
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

        # Extract Cookies
        cookies = info.get("set-cookie", "")
        self.session_cookie = cookies

        # Extract CSRF Token from JWT in TOKEN cookie
        token_cookie = [c for c in cookies.split(",") if "TOKEN=" in c]
        if token_cookie:
            token_val = token_cookie[0].split("TOKEN=")[1].split(";")[0]
            try:
                # We don't verify the signature here as we just need the payload for CSRF
                payload_b64 = token_val.split(".")[1]
                padding = "=" * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.b64decode(payload_b64 + padding).decode("utf-8"))
                self.csrf_token = payload.get("csrfToken")
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
            headers = {"Content-Type": "application/json", "Cookie": self.session_cookie, "X-CSRF-Token": self.csrf_token}
            response, info = self._fetch_with_retry(url, method, headers, payload)

        if info["status"] not in [200, 201, 204]:
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
