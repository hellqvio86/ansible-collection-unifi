import base64
import json

from ansible.module_utils.urls import fetch_url

try:
    import jwt  # noqa: F401

    HAS_JWT = True
except ImportError:
    HAS_JWT = False


class UnifiAPI:
    def __init__(self, module, host, username, password, validate_certs=False):
        self.module = module
        self.host = host
        self.username = username
        self.password = password
        self.validate_certs = validate_certs
        self.session_cookie = None
        self.csrf_token = None
        self.base_url = f"https://{host}"

    def login(self):
        login_url = f"{self.base_url}/api/auth/login"
        login_payload = json.dumps({"username": self.username, "password": self.password})

        response, info = fetch_url(
            self.module,
            login_url,
            data=login_payload,
            method="POST",
            headers={"Content-Type": "application/json"},
            validate_certs=self.validate_certs,
        )

        if info["status"] != 200:
            self.module.fail_json(msg=f"Login failed: {info.get('msg', 'Unknown error')}")

        # Extract Cookies
        cookies = info.get("set-cookie", "")
        self.session_cookie = cookies

        # Extract CSRF Token from JWT in TOKEN cookie
        token_cookie = [c for c in cookies.split(",") if "TOKEN=" in c]
        if token_cookie:
            token_val = token_cookie[0].split("TOKEN=")[1].split(";")[0]
            try:
                # We don't verify the signature here as we just need the payload for CSRF
                # jwt.decode with verify=False or manual base64 decode
                payload_b64 = token_val.split(".")[1]
                padding = "=" * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.b64decode(payload_b64 + padding).decode("utf-8"))
                self.csrf_token = payload.get("csrfToken")
            except Exception as e:
                self.module.fail_json(msg=f"Failed to decode JWT for CSRF: {str(e)}")

        return True

    def request(self, path, method="GET", data=None):
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json", "Cookie": self.session_cookie, "X-CSRF-Token": self.csrf_token}

        payload = json.dumps(data) if data else None
        response, info = fetch_url(
            self.module, url, data=payload, method=method, headers=headers, validate_certs=self.validate_certs
        )

        if info["status"] not in [200, 201, 204]:
            return None, info

        res_data = response.read()
        try:
            return json.loads(res_data) if res_data else {}, info
        except ValueError:
            return res_data, info
