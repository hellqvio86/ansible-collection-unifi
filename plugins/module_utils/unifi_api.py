# Note: debug/ is a working directory, it will not be committed, therefore it will not be a part of the next review.

import base64
import hashlib
import ipaddress as _ipaddress
import json
import os
import random
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


# In-memory tracking of the last request timestamp per host for inter-request delay
_HOST_LAST_REQUEST: dict[str, float] = {}


def scrub_secrets(text: str | None, secrets: list[str | None] | None = None) -> str:
    """Scrub sensitive credentials, tokens, and private keys from error messages."""
    if not text:
        return ""
    cleaned = str(text)

    # 1. Scrub explicit known secrets
    if secrets:
        for secret in secrets:
            if secret and len(secret) > 2 and secret in cleaned:
                cleaned = cleaned.replace(secret, "********")

    # 2. Scrub PEM Private Keys
    cleaned = re.sub(
        r"-----BEGIN [A-Z0-9_-]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9_-]+ PRIVATE KEY-----",
        "[PRIVATE KEY REDACTED]",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 3. Scrub key-value secrets (e.g. password=..., token=..., api_key=..., passphrase=...)
    cleaned = re.sub(
        r"(?i)\b(password|token|api[_-]?key|secret|passphrase)\b(\s*[:=]\s*)([\"']?)([^\s,\"']+)([\"']?)",
        r"\1\2\3********\5",
        cleaned,
    )

    # 4. Scrub Bearer tokens
    cleaned = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer ********", cleaned)

    # 5. Scrub JWT tokens (three dot-separated base64url parts)
    cleaned = re.sub(r"ey[A-Za-z0-9_-]{10,}\.ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+", "********", cleaned)

    return cleaned


def categorize_endpoint(endpoint: str | None) -> str:
    """Determine a safe, high-level endpoint category from an API endpoint/URL."""
    if not endpoint:
        return "general"
    ep = endpoint.lower()
    if "/api/auth" in ep or "login" in ep:
        return "auth"
    if "firewall" in ep:
        return "firewall"
    if "wlan" in ep or "wifi" in ep:
        return "wlan"
    if "portforward" in ep:
        return "port_forward"
    if "portconf" in ep or "port" in ep:
        return "port_profile"
    if "certificate" in ep or "ssl" in ep:
        return "certificate"
    if "nat" in ep:
        return "nat"
    if "device" in ep:
        return "device"
    if "/sta" in ep or "alluser" in ep:
        return "client"
    if "networkconf" in ep:
        return "network"
    if "user" in ep:
        return "user"
    if "rsyslog" in ep or "syslog" in ep:
        return "system"
    if "setting" in ep or "system" in ep:
        return "system"
    if "network" in ep:
        return "network"
    return "api"


def sanitize_api_error(
    info: dict[str, Any] | None,
    endpoint: str | None = None,
    known_secrets: list[str | None] | None = None,
) -> dict[str, Any]:
    """Format and sanitize API error responses.

    Returns only the status code, endpoint category, and a safe controller error message.
    Explicitly excludes headers, cookies, authorization tokens, URLs, and raw payloads.
    """
    if not isinstance(info, dict):
        return {
            "status": -1,
            "category": categorize_endpoint(endpoint),
            "endpoint_category": categorize_endpoint(endpoint),
            "msg": scrub_secrets("Unknown API error", known_secrets),
        }

    status = info.get("status", -1)
    category = categorize_endpoint(endpoint or info.get("url"))

    safe_msg = ""
    body = info.get("body")
    if body:
        if isinstance(body, (bytes, bytearray)):
            try:
                body = body.decode("utf-8", errors="replace")
            except Exception:
                body = ""
        if isinstance(body, str):
            try:
                body_json = json.loads(body)
                if isinstance(body_json, dict):
                    meta = body_json.get("meta")
                    if isinstance(meta, dict) and meta.get("msg"):
                        safe_msg = str(meta["msg"])
                    elif body_json.get("message"):
                        safe_msg = str(body_json["message"])
                    elif body_json.get("error"):
                        safe_msg = str(body_json["error"])
                    elif body_json.get("msg"):
                        safe_msg = str(body_json["msg"])
            except Exception:
                pass

    if not safe_msg:
        safe_msg = str(info.get("msg") or "API request failed")

    safe_msg = scrub_secrets(safe_msg, known_secrets)

    return {
        "status": status,
        "category": category,
        "endpoint_category": category,
        "msg": safe_msg,
    }


format_api_error = sanitize_api_error


def _sanitize_info(info: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(info, dict):
        return info
    sanitized = dict(info)
    for key in list(sanitized.keys()):
        if key.lower() in ("set-cookie", "cookie", "authorization", "x-api-key", "x-csrf-token"):
            sanitized[key] = "********"
    return sanitized


class AuthMode:
    API_KEY = "api_key"
    SESSION = "session"
    USER_PASS = "user_pass"
    NONE = "none"


def sanitize_diff(obj: Any) -> Any:
    """Recursively scrub sensitive keys from dictionaries and lists for diffs."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("password", "passphrase", "secret", "token", "api_key", "key", "cert", "psk")):
                sanitized[k] = "********"
            else:
                sanitized[k] = sanitize_diff(v)
        return sanitized
    if isinstance(obj, list):
        return [sanitize_diff(item) for item in obj]
    return obj


def make_diff(before: Any, after: Any) -> dict[str, Any]:
    """Create a sanitized diff dictionary for Ansible diff mode."""
    return {
        "before": sanitize_diff(before) if before is not None else {},
        "after": sanitize_diff(after) if after is not None else {},
    }


def find_resource(
    module: Any,
    resources: list[Any],
    resource_type: str,
    name: str | None = None,
    resource_id: str | None = None,
    natural_key_field: str = "name",
    extra_criteria: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Find a single resource by immutable id or natural key (e.g. name).

    Returns:
        - None if 0 matches
        - dict if exactly 1 match
        - fails via module.fail_json if multiple matches exist
    """
    if resource_id:
        id_matches = [
            r
            for r in resources
            if isinstance(r, dict) and (r.get("_id") == resource_id or r.get("id") == resource_id)
        ]
        if len(id_matches) > 1:
            module.fail_json(
                msg=f"Ambiguous resource: multiple {resource_type} resources match id '{resource_id}'"
            )
        if id_matches:
            return id_matches[0]
        return None

    if name is not None:
        matches = []
        for r in resources:
            if not isinstance(r, dict):
                continue
            if r.get(natural_key_field) != name:
                continue
            if extra_criteria:
                mismatch = False
                for k, v in extra_criteria.items():
                    if r.get(k) != v:
                        mismatch = True
                        break
                if mismatch:
                    continue
            matches.append(r)

        if len(matches) > 1:
            crit_desc = f" with {extra_criteria}" if extra_criteria else ""
            module.fail_json(
                msg=f"Ambiguous resource: multiple {resource_type} resources match {natural_key_field} '{name}'{crit_desc}. "
                "Specify 'id' or resolve duplicate resources on the controller."
            )
        return matches[0] if matches else None

    return None


SERVER_GENERATED_KEYS: frozenset[str] = frozenset(
    {
        "_id",
        "id",
        "site_id",
        "attr_no_delete",
        "attr_hidden_id",
        "setting_preference",
        "version",
        "datetime",
        "_uptime",
        "uptime",
        "last_seen",
        "stat",
        "meta",
    }
)


def normalize_ports(val: Any) -> set[str] | None:
    """Parse port or comma-separated ports into a normalized set of strings."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return {str(int(val))}
    if isinstance(val, str):
        parts = [p.strip() for p in val.split(",") if p.strip()]
        return set(parts) if parts else {""}
    if isinstance(val, (list, set, tuple)):
        return {str(p).strip() for p in val if p is not None}
    return None


def canonical_compare(existing: Any, desired: Any, sort_lists: bool = True) -> bool:
    """Compare an existing controller attribute with a desired attribute.

    Returns True if the values are considered equivalent (no drift).
    Handles:
    - Type coercions (int vs string number, e.g. 514 vs '514')
    - None vs empty string equivalence
    - Port lists / comma-separated port normalization ('80, 443' == '443,80')
    - Unordered list equivalence (['2g', '5g'] == ['5g', '2g'])
    - Recursive dictionary comparison ignoring server-generated metadata
    """
    if existing is desired:
        return True

    # Empty string vs None equivalence for optional text fields
    if existing in (None, "") and desired in (None, ""):
        return True

    # Boolean vs exact type
    if isinstance(desired, bool) or isinstance(existing, bool):
        if isinstance(desired, bool) and isinstance(existing, bool):
            return desired == existing
        if isinstance(existing, str):
            existing_bool = existing.lower() in ("true", "1", "yes", "on")
            return existing_bool == desired
        if isinstance(desired, str):
            desired_bool = desired.lower() in ("true", "1", "yes", "on")
            return desired_bool == existing

    # Numeric coercion (e.g. 86400 vs '86400', 514 vs '514')
    if isinstance(desired, (int, float)) and isinstance(existing, str):
        try:
            return float(existing) == float(desired)
        except (ValueError, TypeError):
            pass
    if isinstance(existing, (int, float)) and isinstance(desired, str):
        try:
            return float(desired) == float(existing)
        except (ValueError, TypeError):
            pass

    # Comma-separated strings or port normalization
    if isinstance(desired, str) and isinstance(existing, str):
        if "," in desired or "," in existing:
            set_des = {s.strip() for s in desired.split(",") if s.strip()}
            set_exist = {s.strip() for s in existing.split(",") if s.strip()}
            if set_des == set_exist:
                return True
        return existing.strip() == desired.strip()

    # Lists
    if isinstance(existing, list) and isinstance(desired, list):
        if len(existing) != len(desired):
            return False
        if sort_lists:
            try:
                sorted_exist = sorted(existing)
                sorted_des = sorted(desired)
                return all(canonical_compare(e, d, sort_lists=True) for e, d in zip(sorted_exist, sorted_des, strict=False))
            except TypeError:
                unmatched_des = list(desired)
                for e in existing:
                    found = False
                    for i, d in enumerate(unmatched_des):
                        if canonical_compare(e, d, sort_lists=True):
                            unmatched_des.pop(i)
                            found = True
                            break
                    if not found:
                        return False
                return len(unmatched_des) == 0
        else:
            return all(canonical_compare(e, d, sort_lists=False) for e, d in zip(existing, desired, strict=False))

    # Dictionaries
    if isinstance(existing, dict) and isinstance(desired, dict):
        for k, v in desired.items():
            if k in SERVER_GENERATED_KEYS:
                continue
            if not canonical_compare(existing.get(k), v, sort_lists=sort_lists):
                return False
        return True

    return existing == desired


def resource_has_drift(
    existing: dict[str, Any] | None,
    desired: dict[str, Any],
    ignored_keys: set[str] | None = None,
    sort_lists: bool = True,
) -> bool:
    """Return True if desired state differs from existing controller state.

    Ignores server-generated keys and accounts for list ordering and type conversions.
    """
    if not existing:
        return True

    ignored = SERVER_GENERATED_KEYS | (ignored_keys or set())
    for key, desired_val in desired.items():
        if key in ignored:
            continue
        existing_val = existing.get(key)
        if not canonical_compare(existing_val, desired_val, sort_lists=sort_lists):
            return True

    return False


class ControllerVersion:
    """Represents a parsed semantic version for UniFi controllers."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.major = 0
        self.minor = 0
        self.patch = 0
        m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", raw)
        if m:
            self.major = int(m.group(1))
            self.minor = int(m.group(2))
            self.patch = int(m.group(3)) if m.group(3) else 0

    def __ge__(self, other: "ControllerVersion | tuple[int, ...]") -> bool:
        if isinstance(other, tuple):
            return (self.major, self.minor, self.patch) >= other
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __lt__(self, other: "ControllerVersion | tuple[int, ...]") -> bool:
        if isinstance(other, tuple):
            return (self.major, self.minor, self.patch) < other
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __repr__(self) -> str:
        return f"ControllerVersion({self.raw})"


class UnifiCompatibility:
    """Version and feature compatibility layer for UniFi controllers."""

    MIN_NETWORK_VERSION = (7, 0, 0)
    MIN_POLICY_ENGINE_VERSION = (8, 0, 0)
    MIN_UNIFI_OS_VERSION = (3, 0, 0)

    @classmethod
    def parse_version(cls, version_str: str | None) -> ControllerVersion | None:
        if not version_str:
            return None
        return ControllerVersion(version_str)

    @classmethod
    def check_policy_engine_support(cls, version_str: str | None) -> tuple[bool, str | None]:
        if not version_str:
            return True, None
        v = cls.parse_version(version_str)
        if v and v < cls.MIN_POLICY_ENGINE_VERSION:
            return False, (
                f"UniFi Network version '{version_str}' does not support the Policy Engine (v2 API). "
                f"Minimum required version is 8.0.0."
            )
        return True, None

    @classmethod
    def check_user_certificate_support(cls, os_version_str: str | None) -> tuple[bool, str | None]:
        if not os_version_str:
            return True, None
        v = cls.parse_version(os_version_str)
        if v and v < cls.MIN_UNIFI_OS_VERSION:
            return False, (
                f"UniFi OS version '{os_version_str}' does not support user certificate management. "
                f"Minimum required version is 3.0.0."
            )
        return True, None


class UnifiEndpoints:
    """Centralized UniFi API endpoint paths and constructors.

    Endpoint Families:
    - Legacy REST API (/proxy/network/api/s/{site}/rest/...): Supported across UniFi Network 7.x-9.x.
      Used for WLANs, port profiles, networks, clients, devices, and legacy firewall groups.
    - Policy Engine v2 API (/proxy/network/v2/api/site/{site}/...): Introduced in UniFi Network 8.0+.
      Used for modern zone-based firewall rules, firewall zones, and advanced NAT rules on UDM/UXG.
    - UniFi OS Core API (/api/...): System management endpoints on UniFi OS 3.x/4.x.
      Used for local authentication and user certificates.
    """

    AUTH_LOGIN = "/api/auth/login"
    USER_CERTIFICATES = "/api/userCertificates"

    @classmethod
    def auth_login(cls) -> str:
        return cls.AUTH_LOGIN

    @classmethod
    def user_certificates(cls, resource_id: str | None = None) -> str:
        base = cls.USER_CERTIFICATES
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def wlan(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/wlanconf"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def port_profile(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/portconf"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def network_conf(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/networkconf"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def user(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/user"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def device(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/stat/device"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def port_forward(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/portforward"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def firewall_group(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/api/s/{site}/rest/firewallgroup"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def firewall_zone(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/v2/api/site/{site}/firewall-zone"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def firewall_policy(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/v2/api/site/{site}/firewall-rule"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def nat_rule(site: str = "default", resource_id: str | None = None) -> str:
        base = f"/proxy/network/v2/api/site/{site}/nat/rule"
        return f"{base}/{resource_id}" if resource_id else base

    @staticmethod
    def setting(section: str, site: str = "default") -> str:
        return f"/proxy/network/api/s/{site}/rest/setting/{section}"


class UnifiTransport:
    """HTTP transport layer handling connection, locking, rate limiting, and retries.

    Ubiquiti UniFi APIs are sensitive to concurrent request spikes; without rate limiting,
    concurrent tasks or parallel Ansible executions can overwhelm the Ubiquiti API, causing
    dropped connections, HTTP 429 errors, or daemon instability.
    """

    def __init__(
        self,
        module: Any,
        host: str,
        validate_certs: bool = True,
        ca_path: str | None = None,
        timeout: int = 30,
        retries: int = 5,
        backoff_factor: float = 1.5,
        rate_limit_delay: float = 0.05,
        lock_timeout: float = 30.0,
    ) -> None:
        self.module = module
        self.host = host
        self.base_url = f"https://{self.host}"
        self.validate_certs = validate_certs
        self.ca_path = ca_path
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.rate_limit_delay = rate_limit_delay
        self.lock_timeout = lock_timeout

    @contextmanager
    def host_lock(self):
        """Acquire a per-host lock in the temporary directory for cross-process rate limiting."""
        if not HAS_FCNTL or not self.host:
            yield
            return

        host_hash = hashlib.sha256(self.host.strip().lower().encode("utf-8")).hexdigest()[:12]
        lock_path = os.path.join(tempfile.gettempdir(), f"ansible_unifi_{host_hash}.lock")
        lock_fd = None
        acquired = False
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except (BlockingIOError, OSError):
                    if time.time() - start_time >= self.lock_timeout:
                        if hasattr(self.module, "warn") and callable(self.module.warn):
                            self.module.warn(
                                f"Lock acquisition for host '{self.host}' timed out after {self.lock_timeout}s. "
                                "Proceeding without lock."
                            )
                        break
                    time.sleep(0.05)
        except Exception:
            pass

        try:
            # Smooth rate limiting: minimum delay between consecutive requests to the same host
            if self.rate_limit_delay > 0:
                last_time = _HOST_LAST_REQUEST.get(self.host, 0.0)
                elapsed = time.time() - last_time
                if elapsed < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - elapsed)
            yield
        finally:
            _HOST_LAST_REQUEST[self.host] = time.time()
            if lock_fd is not None:
                try:
                    if acquired:
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except Exception:
                    pass

    @staticmethod
    def is_safe_method(method: str) -> bool:
        """Safe methods do not mutate server state and can be retried safely."""
        return method.upper() in ("GET", "HEAD", "OPTIONS")

    @staticmethod
    def is_idempotent_method(method: str) -> bool:
        """Idempotent methods can be repeated with identical side effects."""
        return method.upper() in ("GET", "HEAD", "OPTIONS", "PUT", "DELETE")

    def should_retry(self, method: str, status: int, is_login: bool = False) -> bool:
        """Determine whether an HTTP request should be retried.

        - 429 (Rate limited): Retryable for all methods once backoff/Retry-After elapses.
        - 502, 503, 504 (Transient gateway errors): Safe for idempotent methods (GET/HEAD/PUT/DELETE)
          and login POST.
        - Non-idempotent POST mutations are NOT retried on 5xx to avoid duplicate resource creation.
        """
        if status == 429:
            return True
        if status in (502, 503, 504):
            if is_login or self.is_idempotent_method(method):
                return True
        return False

    def fetch_with_retry(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        payload: str | None = None,
        is_login: bool = False,
    ) -> tuple[Any, dict[str, Any]]:
        backoff = self.backoff_factor
        for attempt in range(self.retries + 1):
            with self.host_lock():
                response, info = fetch_url(
                    self.module,
                    url,
                    data=payload,
                    method=method,
                    headers=headers,
                    timeout=self.timeout,
                    ca_path=self.ca_path,
                )

            status = info.get("status")
            if not self.should_retry(method, status, is_login=is_login):
                return response, info

            if attempt < self.retries:
                # Check for Retry-After header
                retry_after_hdr = info.get("retry-after") or info.get("Retry-After")
                sleep_time = None
                if retry_after_hdr is not None:
                    try:
                        sleep_time = min(60.0, float(retry_after_hdr))
                    except (ValueError, TypeError):
                        sleep_time = None

                if sleep_time is None:
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = min(30.0, backoff) + jitter
                    backoff *= 2

                time.sleep(sleep_time)

        return response, info


class UnifiAuth:
    """Manages UniFi credentials, token extraction, and session login."""

    def __init__(
        self,
        module: Any,
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
        session_cookie: str | None = None,
        csrf_token: str | None = None,
    ) -> None:
        self.module = module
        self.username = username
        self.password = password
        self.api_key = api_key
        self.session_cookie = session_cookie
        self.csrf_token = csrf_token

    @property
    def auth_mode(self) -> str:
        if self.api_key:
            return AuthMode.API_KEY
        if self.username and self.password:
            return AuthMode.USER_PASS
        if self.session_cookie and self.csrf_token:
            return AuthMode.SESSION
        return AuthMode.NONE

    def get_auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth_mode == AuthMode.API_KEY:
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
        elif self.auth_mode in (AuthMode.SESSION, AuthMode.USER_PASS):
            if self.session_cookie:
                headers["Cookie"] = self.session_cookie
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
        return headers

    def known_secrets(self) -> list[str]:
        secrets: list[str | None] = [self.password, self.api_key, self.session_cookie, self.csrf_token]
        return [s for s in secrets if s]

    def clear_session(self) -> None:
        self.session_cookie = None
        self.csrf_token = None

    def login(self, transport: UnifiTransport) -> bool:
        if self.auth_mode == AuthMode.API_KEY:
            return True
        if self.auth_mode == AuthMode.SESSION:
            return True
        if self.auth_mode == AuthMode.NONE:
            self.module.fail_json(
                msg=(
                    "UniFi authentication credentials not provided. Set 'api_key' (recommended for UniFi OS 3.x+), "
                    "'username'/'password', or pre-authenticated 'unifi_session_cookie'/'unifi_csrf_token'."
                )
            )

        login_url = f"{transport.base_url}/api/auth/login"
        login_payload = json.dumps({"username": self.username, "password": self.password})

        response, info = transport.fetch_with_retry(
            login_url,
            "POST",
            {"Content-Type": "application/json"},
            login_payload,
            is_login=True,
        )

        if info.get("status") != 200:
            status = info.get("status")
            err_info = sanitize_api_error(info, endpoint="/api/auth/login", known_secrets=self.known_secrets())
            if status == 429:
                self.module.fail_json(
                    msg=(
                        "UniFi login rate limit reached. Wait a few minutes before retrying; "
                        "the module stops after this single login attempt."
                    ),
                    info=err_info,
                )
            if status in [401, 403]:
                self.module.fail_json(
                    msg="UniFi login failed: invalid credentials or account not permitted for local API login.",
                    info=err_info,
                )
            self.module.fail_json(msg=f"Login failed: {err_info.get('msg', 'Unknown error')}", info=err_info)

        # 1. Parse Set-Cookie headers into SimpleCookie jar
        set_cookie_raw = info.get("set-cookie") or info.get("Set-Cookie") or ""
        cookie_list = set_cookie_raw if isinstance(set_cookie_raw, list) else [str(set_cookie_raw)]

        cookie_jar = SimpleCookie()
        for item in cookie_list:
            if item:
                try:
                    cookie_jar.load(item)
                except Exception:
                    pass

        if cookie_jar:
            self.session_cookie = "; ".join(f"{k}={morsel.value}" for k, morsel in cookie_jar.items())
        else:
            self.session_cookie = "; ".join(cookie_list) if cookie_list else None

        # 2. Extract CSRF token with clear priority:
        # Priority A: Check direct response headers
        self.csrf_token = (
            info.get("x-csrf-token") or info.get("X-CSRF-Token") or info.get("csrf-token") or info.get("Csrf-Token")
        )

        # Priority B: Check JSON response body
        if not self.csrf_token and response is not None:
            try:
                resp_bytes = response.read()
                if resp_bytes:
                    resp_json = json.loads(resp_bytes.decode("utf-8"))
                    if isinstance(resp_json, dict):
                        self.csrf_token = resp_json.get("csrfToken") or resp_json.get("csrf_token")
            except Exception:
                pass

        # Priority C: Check dedicated CSRF cookie in cookie jar
        if not self.csrf_token:
            for cookie_name in ("csrf_token", "CSRF-TOKEN", "csrfToken", "X-CSRF-TOKEN"):
                if cookie_name in cookie_jar:
                    self.csrf_token = cookie_jar[cookie_name].value
                    break

        # Priority D: Decode controller-issued TOKEN JWT cookie without external pyjwt dependency
        # Security rationale: In UniFi session auth, the controller embeds the CSRF token
        # claim inside the TOKEN cookie. Decoding the unencrypted payload using stdlib base64/json
        # is safe because the token was issued directly over TLS by the controller,
        # and the controller cryptographically verifies the token signature on incoming requests.
        if not self.csrf_token:
            token_val = None
            if "TOKEN" in cookie_jar:
                token_val = cookie_jar["TOKEN"].value
            elif cookie_list:
                m = re.search(r"(?:^|;\s*|\b)TOKEN=([^;]+)", "; ".join(cookie_list))
                if m:
                    token_val = m.group(1)

            if token_val:
                try:
                    parts = token_val.split(".")
                    if len(parts) >= 2:
                        payload_b64 = parts[1]
                        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
                        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
                        payload = json.loads(payload_bytes.decode("utf-8"))
                        if isinstance(payload, dict):
                            self.csrf_token = payload.get("csrfToken") or payload.get("csrf_token")
                except Exception:
                    pass

        if not self.csrf_token:
            self.module.fail_json(
                msg="UniFi login succeeded but failed to extract CSRF token from controller response.",
                info=sanitize_api_error(info, endpoint="/api/auth/login", known_secrets=self.known_secrets()),
            )

        return True


@contextmanager
def _host_lock(host: str | None, timeout: float = 30.0, rate_limit_delay: float = 0.05):
    """Acquire a per-host lock in the temporary directory for cross-process rate limiting."""
    transport = UnifiTransport(
        module=None,
        host=host or "",
        lock_timeout=timeout,
        rate_limit_delay=rate_limit_delay,
    )
    with transport.host_lock():
        yield


class UnifiAPI:
    """Unified UniFi API client composing Transport, Auth, and Resource handling."""

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
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.module = module

        param_getter = (
            self.module.params.get
            if hasattr(self.module, "params") and isinstance(self.module.params, dict)
            else lambda k: None
        )

        # Fallback to module parameters or environment variables if not provided
        self.host = host or param_getter("host") or os.environ.get("UNIFI_HOST")
        self.api_key = (
            api_key or param_getter("api_key") or os.environ.get("UNIFI_API_KEY") or os.environ.get("UNIFI_API_TOKEN")
        )
        self.username = username or param_getter("username") or os.environ.get("UNIFI_USERNAME")
        self.password = password or param_getter("password") or os.environ.get("UNIFI_PASSWORD")

        # Handle validate_certs fallback (defaults to True for security)
        if validate_certs is not None:
            self.validate_certs = validate_certs
        else:
            env_val = os.environ.get("UNIFI_VALIDATE_CERTS", "true").lower()
            self.validate_certs = env_val in ["true", "1", "yes", "on"]

        self.ca_path = ca_path or param_getter("ca_path") or os.environ.get("UNIFI_CA_PATH")

        # Resolve timeout
        timeout_val = timeout or param_getter("timeout") or os.environ.get("UNIFI_TIMEOUT") or 30
        try:
            self.timeout = int(timeout_val)
        except (ValueError, TypeError):
            self.timeout = 30

        if not self.host:
            self.module.fail_json(
                msg="UniFi host not provided. Set 'host' parameter or 'UNIFI_HOST' environment variable."
            )

        self.base_url = f"https://{self.host}"

        # Ensure the module has parameters set as expected by fetch_url
        if hasattr(self.module, "params") and isinstance(self.module.params, dict):
            self.module.params["validate_certs"] = self.validate_certs
            if self.ca_path:
                self.module.params["ca_path"] = self.ca_path
            self.module.params["timeout"] = self.timeout

        if not self.validate_certs and hasattr(self.module, "warn") and callable(self.module.warn):
            self.module.warn(
                "Certificate validation is disabled ('validate_certs: false'). "
                "Connection to the UniFi controller is insecure."
            )

        # Internal abstractions
        self.transport = UnifiTransport(
            module=self.module,
            host=self.host,
            validate_certs=self.validate_certs,
            ca_path=self.ca_path,
            timeout=self.timeout,
        )
        self.auth = UnifiAuth(
            module=self.module,
            username=self.username,
            password=self.password,
            api_key=self.api_key,
            session_cookie=session_cookie or param_getter("unifi_session_cookie"),
            csrf_token=csrf_token or param_getter("unifi_csrf_token"),
        )

    @property
    def session_cookie(self) -> str | None:
        return self.auth.session_cookie

    @session_cookie.setter
    def session_cookie(self, value: str | None) -> None:
        self.auth.session_cookie = value

    @property
    def csrf_token(self) -> str | None:
        return self.auth.csrf_token

    @csrf_token.setter
    def csrf_token(self, value: str | None) -> None:
        self.auth.csrf_token = value

    @property
    def auth_mode(self) -> str:
        return self.auth.auth_mode

    def get_auth_headers(self) -> dict[str, str]:
        return self.auth.get_auth_headers()

    def _known_secrets(self) -> list[str]:
        return self.auth.known_secrets()

    def sanitize_error(self, info: dict[str, Any] | None, endpoint: str | None = None) -> dict[str, Any]:
        return sanitize_api_error(info, endpoint=endpoint, known_secrets=self._known_secrets())

    def login(self) -> bool:
        return self.auth.login(self.transport)

    def _fetch_with_retry(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        payload: str | None,
        is_login: bool = False,
    ):
        return self.transport.fetch_with_retry(url, method, headers, payload, is_login=is_login)

    def request(
        self, path: str, method: str = "GET", data: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any] | bytes | None, dict[str, Any]]:
        # Hard check mode mutation guard: ensure zero mutating API requests happen in check mode
        if (
            hasattr(self.module, "check_mode")
            and self.module.check_mode
            and method.upper() in ["POST", "PUT", "PATCH", "DELETE"]
            and not path.startswith("/api/auth")
        ):
            self.module.fail_json(
                msg=f"Internal collection error: mutating request {method} {path} attempted during check mode"
            )

        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        headers.update(self.get_auth_headers())

        payload = json.dumps(data) if data else None
        response, info = self.transport.fetch_with_retry(url, method, headers, payload)

        if info.get("status") in [401, 403] and self.auth_mode == AuthMode.USER_PASS:
            self.auth.clear_session()
            self.login()
            headers = {"Content-Type": "application/json"}
            headers.update(self.get_auth_headers())
            response, info = self.transport.fetch_with_retry(url, method, headers, payload)

        if info.get("status") not in [200, 201, 204]:
            return None, self.sanitize_error(info, endpoint=path)

        sanitized_info = _sanitize_info(info) or {}

        if response is None:
            return {}, sanitized_info

        res_data = response.read()
        try:
            return json.loads(res_data) if res_data else {}, sanitized_info
        except ValueError:
            return res_data, sanitized_info

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

    def find_resource(
        self,
        resources: list[Any],
        resource_type: str,
        name: str | None = None,
        resource_id: str | None = None,
        natural_key_field: str = "name",
        extra_criteria: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return find_resource(
            self.module,
            resources,
            resource_type,
            name=name,
            resource_id=resource_id,
            natural_key_field=natural_key_field,
            extra_criteria=extra_criteria,
        )

    def get_network_version(self, site: str = "default") -> str | None:
        """Fetch the UniFi Network application version."""
        res, _ = self.request(f"/proxy/network/api/s/{site}/stat/sysinfo")
        if isinstance(res, dict):
            data = res.get("data")
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data[0].get("version")
        return None

    def get_os_version(self) -> str | None:
        """Fetch the UniFi OS system version."""
        res, _ = self.request("/api/system/info")
        if isinstance(res, dict):
            return res.get("version")
        return None

    def validate_feature_support(self, feature: str, site: str = "default") -> None:
        """Validate that the connected controller supports a given feature."""
        if feature == "policy_engine":
            version = self.get_network_version(site)
            supported, err = UnifiCompatibility.check_policy_engine_support(version)
            if not supported and err:
                self.module.fail_json(msg=err)
        elif feature == "user_certificates":
            version = self.get_os_version()
            supported, err = UnifiCompatibility.check_user_certificate_support(version)
            if not supported and err:
                self.module.fail_json(msg=err)


def unifi_argument_spec() -> dict[str, dict[str, Any]]:
    """Return common argument specification dictionary for UniFi modules."""
    return dict(
        host=dict(type="str"),
        username=dict(type="str", no_log=True),
        password=dict(type="str", no_log=True),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
        api_key=dict(type="str", no_log=True, required=False),
        unifi_session_cookie=dict(type="str", no_log=True, required=False),
        unifi_csrf_token=dict(type="str", no_log=True, required=False),
        timeout=dict(type="int", default=30),
    )


# ---------------------------------------------------------------------------
# Argument validation helpers (8.x)
# ---------------------------------------------------------------------------

def validate_ip_address(module: Any, value: str, param_name: str) -> str:
    """Validate that *value* is a well-formed IPv4 or IPv6 address.

    Returns the normalized (compressed) string form.
    Calls ``module.fail_json`` with a clear message on failure.
    """
    if not value:
        return value
    try:
        return str(_ipaddress.ip_address(value))
    except ValueError:
        module.fail_json(msg=f"Invalid IP address for '{param_name}': {value!r}")


def validate_cidr(module: Any, value: str, param_name: str) -> str:
    """Validate that *value* is a well-formed IP address or CIDR network.

    Accepts plain IPs (host addresses) as well as CIDR notation.
    Returns the normalized string form.
    Calls ``module.fail_json`` with a clear message on failure.
    """
    if not value:
        return value
    try:
        # Try plain IP first
        return str(_ipaddress.ip_address(value))
    except ValueError:
        pass
    try:
        # Try CIDR network (strict=False allows host bits to be set)
        net = _ipaddress.ip_network(value, strict=False)
        return str(net)
    except ValueError:
        module.fail_json(msg=f"Invalid IP address or CIDR for '{param_name}': {value!r}")


def validate_port(module: Any, value: Any, param_name: str) -> int:
    """Validate that *value* is a valid TCP/UDP port number (1–65535).

    Returns the port as an integer.
    Calls ``module.fail_json`` with a clear message on failure.
    """
    try:
        port = int(value)
    except (TypeError, ValueError):
        module.fail_json(msg=f"Invalid port for '{param_name}': {value!r} — must be an integer")
        return 0  # unreachable but satisfies type checkers
    if not 1 <= port <= 65535:
        module.fail_json(msg=f"Invalid port for '{param_name}': {value!r} — must be 1–65535")
    return port


def validate_port_range(module: Any, value: str, param_name: str) -> str:
    """Validate that *value* is a valid port or port range string (e.g. '80', '8000-8080').

    Returns the value unchanged if valid.
    Calls ``module.fail_json`` with a clear message on failure.
    """
    if not value:
        return value
    parts = str(value).split("-")
    if len(parts) == 1:
        validate_port(module, parts[0].strip(), param_name)
    elif len(parts) == 2:
        lo = validate_port(module, parts[0].strip(), param_name)
        hi = validate_port(module, parts[1].strip(), param_name)
        if lo > hi:
            module.fail_json(
                msg=f"Invalid port range for '{param_name}': {value!r} — start port must be ≤ end port"
            )
    else:
        module.fail_json(msg=f"Invalid port range for '{param_name}': {value!r}")
    return value


def validate_mac_address(module: Any, value: str, param_name: str) -> str:
    """Validate and normalize a MAC address to lowercase colon-separated form.

    Accepts common formats: ``aa:bb:cc:dd:ee:ff``, ``aa-bb-cc-dd-ee-ff``, ``aabbccddeeff``.
    Returns the normalized ``aa:bb:cc:dd:ee:ff`` form.
    Calls ``module.fail_json`` with a clear message on failure.
    """
    if not value:
        return value
    # Normalize separators
    normalized = re.sub(r"[-.]", ":", value.strip().lower())
    # Remove separators to validate hex digits
    hex_only = normalized.replace(":", "")
    if len(hex_only) != 12 or not all(c in "0123456789abcdef" for c in hex_only):
        module.fail_json(msg=f"Invalid MAC address for '{param_name}': {value!r}")
    # Rebuild as colon-separated pairs
    return ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))
