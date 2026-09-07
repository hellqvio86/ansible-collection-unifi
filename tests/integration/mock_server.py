# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class MockUniFiState:
    """Stateful in-memory representation of a UniFi Controller."""

    def __init__(self) -> None:
        self.valid_username = "admin"
        self.valid_password = "secretpassword"
        self.valid_api_key = "test-api-key"
        self.session_token = "session_cookie_abc"
        self.csrf_token = "extracted_csrf_token_123"

        self.reset()

    def reset(self) -> None:
        """Reset state to baseline initial UniFi state."""
        self.requests_log: list[dict[str, Any]] = []

        # Default site data
        self.sites: dict[str, dict[str, list[dict[str, Any]]]] = {
            "default": {
                "networkconf": [
                    {
                        "_id": "net_default_lan",
                        "name": "Default LAN",
                        "purpose": "corporate",
                        "ip_subnet": "192.168.1.1/24",
                        "vlan_enabled": False,
                        "dhcpd_enabled": True,
                        "dhcp_start": "192.168.1.6",
                        "dhcp_stop": "192.168.1.254",
                        "dhcpd_dns_1": "192.168.1.1",
                    }
                ],
                "firewallgroup": [],
                "firewall/zone": [
                    {
                        "id": "zone_internal",
                        "_id": "zone_internal",
                        "name": "Internal",
                        "network_ids": ["net_default_lan"],
                        "ip_subnets": [],
                    },
                    {
                        "id": "zone_external",
                        "_id": "zone_external",
                        "name": "External",
                        "network_ids": [],
                        "ip_subnets": [],
                    },
                ],
                "firewall-policies": [],
                "nat": [],
                "nat/rules": [],
                "portforward": [],
                "portconf": [
                    {
                        "_id": "pc_all",
                        "name": "All",
                        "forward": "all",
                        "native_networkconf_id": "net_default_lan",
                    }
                ],
                "switchprofile": [
                    {
                        "_id": "sw_all",
                        "name": "All",
                        "site_id": "default",
                        "native_networkconf_id": "net_default_lan",
                    }
                ],
                "wlanconf": [],
                "device": [
                    {
                        "_id": "dev_switch_1",
                        "mac": "00:11:22:33:44:55",
                        "name": "Core-Switch-24",
                        "model": "USW-24-PoE",
                        "type": "usw",
                        "port_table": [
                            {"port_idx": 1, "name": "Port 1", "portconf_id": "pc_all"},
                            {"port_idx": 2, "name": "Port 2", "portconf_id": "pc_all"},
                        ],
                        "port_overrides": [],
                    }
                ],
                "alluser": [
                    {
                        "_id": "client_printer_1",
                        "mac": "aa:bb:cc:dd:ee:ff",
                        "name": "Office Printer",
                        "hostname": "printer",
                        "use_fixedip": False,
                    }
                ],
                "setting": [
                    {
                        "_id": "set_rsyslog_1",
                        "key": "rsyslogd",
                        "enabled": False,
                        "ip": "192.168.1.50",
                        "port": 514,
                    },
                    {
                        "_id": "set_mgmt_1",
                        "key": "mgmt",
                        "x_ssh_bind_wildcard": True,
                        "x_ssh_keys": [],
                        "led_enabled": True,
                    },
                    {
                        "_id": "set_ntp_1",
                        "key": "ntp",
                        "ntp_server_1": "0.pool.ntp.org",
                        "timezone": "UTC",
                    },
                    {
                        "_id": "set_switch_1",
                        "key": "global_switch",
                        "dhcp_snoop": False,
                        "flowctrl_enabled": False,
                        "jumboframe_enabled": False,
                    },
                ],
            }
        }

        # Global console / system resources
        self.users_self: dict[str, Any] = {
            "id": "user_admin",
            "username": "admin",
            "sshKeys": [],
        }
        self.user_certificates: list[dict[str, Any]] = []

    def get_site_collection(self, site: str, collection: str) -> list[dict[str, Any]]:
        if site not in self.sites:
            self.sites[site] = {
                "networkconf": [],
                "firewallgroup": [],
                "firewall/zone": [],
                "firewall-policies": [],
                "nat": [],
                "nat/rules": [],
                "portforward": [],
                "portconf": [],
                "switchprofile": [],
                "wlanconf": [],
                "device": [],
                "alluser": [],
                "setting": [],
            }
        if collection not in self.sites[site]:
            self.sites[site][collection] = []
        return self.sites[site][collection]


class MockUniFiRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request handler for stateful UniFi Mock Controller."""

    # Attached at server startup
    state: MockUniFiState

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default standard error logging during tests
        pass

    def _read_body(self) -> dict[str, Any] | None:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len <= 0:
            return None
        raw_body = self.rfile.read(content_len).decode("utf-8")
        try:
            return json.loads(raw_body)
        except Exception:
            return None

    def _send_json(self, status_code: int, data: Any, extra_headers: dict[str, str] | None = None) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        response_bytes = json.dumps(data).encode("utf-8")
        self.wfile.write(response_bytes)

    def _send_unauthorized(self, msg: str = "Unauthorized") -> None:
        self._send_json(401, {"meta": {"rc": "error", "msg": msg}})

    def _is_authenticated(self) -> bool:
        # 1. Check API Key
        api_key_hdr = self.headers.get("X-API-KEY") or self.headers.get("x-api-key")
        if api_key_hdr and api_key_hdr == self.state.valid_api_key:
            return True

        # 2. Check Cookie + CSRF
        cookie_hdr = self.headers.get("Cookie", "")
        csrf_hdr = self.headers.get("X-CSRF-Token", "")
        if f"SESSION={self.state.session_token}" in cookie_hdr:
            if csrf_hdr == self.state.csrf_token:
                return True

        return False

    def _normalize_path(self, path: str) -> str:
        # Strip query string and proxy prefix
        clean_path = path.split("?")[0]
        if clean_path.startswith("/proxy/network"):
            clean_path = clean_path[len("/proxy/network") :]
        return clean_path

    # -----------------------------------------------------------------------
    # POST Handlers
    # -----------------------------------------------------------------------
    def do_POST(self) -> None:
        path = self._normalize_path(self.path)
        body = self._read_body() or {}
        self.state.requests_log.append({"method": "POST", "path": path, "body": body})

        # 1. Login endpoint
        if path == "/api/auth/login":
            username = body.get("username")
            password = body.get("password")
            if username == self.state.valid_username and password == self.state.valid_password:
                payload = json.dumps({"csrfToken": self.state.csrf_token}).encode("utf-8")
                token = f"header.{base64.urlsafe_b64encode(payload).decode('utf-8')}.sig"

                extra_headers = {
                    "Set-Cookie": (
                        f"TOKEN={token}; Path=/; HttpOnly\r\n"
                        f"Set-Cookie: SESSION={self.state.session_token}; Path=/; Secure"
                    ),
                }
                self._send_json(200, {"meta": {"rc": "ok"}}, extra_headers=extra_headers)
            else:
                self._send_json(401, {"meta": {"rc": "error", "msg": "Invalid credentials"}})
            return

        # Check authentication for all other endpoints
        if not self._is_authenticated():
            self._send_unauthorized()
            return

        # 2. User Certificate upload endpoint (/api/userCertificates)
        if path == "/api/userCertificates":
            cert_id = f"cert_{uuid.uuid4().hex[:8]}"
            cert_pem = body.get("cert", "")
            local_fp = ""
            try:
                pem_parts = cert_pem.split("-----END CERTIFICATE-----")
                if pem_parts and "-----BEGIN CERTIFICATE-----" in pem_parts[0]:
                    b64_lines = [
                        line.strip()
                        for line in pem_parts[0].splitlines()
                        if line.strip() and not line.startswith("-----")
                    ]
                    der = base64.b64decode("".join(b64_lines))
                    sha1_hex = hashlib.sha1(der).hexdigest().upper()
                    local_fp = ":".join(sha1_hex[i : i + 2] for i in range(0, 40, 2))
            except Exception:
                pass

            cert_obj = {
                "id": cert_id,
                "name": body.get("name", "cert"),
                "fingerprint": local_fp,
                "active": body.get("active", True),
                "cert": cert_pem,
            }
            self.state.user_certificates.append(cert_obj)
            self._send_json(201, cert_obj)
            return

        # 3. v2 Policy endpoints
        # /v2/api/site/{site}/firewall/zone
        m = re.match(r"^/v2/api/site/([^/]+)/(firewall/zone|firewall-policies|nat/rules|nat)$", path)
        if m:
            site, collection = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, collection)
            new_item = copy.deepcopy(body)
            new_item["id"] = f"id_{uuid.uuid4().hex[:8]}"
            new_item["_id"] = new_item["id"]
            store.append(new_item)
            self._send_json(201, {"data": [new_item]})
            return

        # 4. Standard REST collection POST (/api/s/{site}/rest/{collection})
        m = re.match(r"^/api/s/([^/]+)/rest/([^/]+)$", path)
        if m:
            site, collection = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, collection)
            new_item = copy.deepcopy(body)
            new_item["_id"] = f"id_{uuid.uuid4().hex[:8]}"
            new_item["site_id"] = site
            store.append(new_item)
            self._send_json(201, {"data": [new_item]})
            return

        # 5. Device manager commands (/api/s/{site}/cmd/devmgr or /cmd/sitemgr)
        m = re.match(r"^/api/s/([^/]+)/cmd/(devmgr|sitemgr)$", path)
        if m:
            site = m.group(1)
            cmd = body.get("cmd")
            mac = body.get("mac", "").lower()
            store = self.state.get_site_collection(site, "device")
            target = next((d for d in store if d.get("mac", "").lower() == mac), None)
            if cmd == "adopt" and target:
                target["adopted"] = True
                target["state"] = 1
            elif cmd == "set-locate" and target:
                target["locating"] = True
            elif cmd == "unset-locate" and target:
                target["locating"] = False
            elif cmd == "delete-device" and target:
                store.remove(target)
            self._send_json(200, {"data": []})
            return

        self._send_json(404, {"meta": {"rc": "error", "msg": f"Endpoint {path} not found"}})

    # -----------------------------------------------------------------------
    # GET Handlers
    # -----------------------------------------------------------------------
    def do_GET(self) -> None:
        path = self._normalize_path(self.path)
        self.state.requests_log.append({"method": "GET", "path": path})

        if not self._is_authenticated():
            self._send_unauthorized()
            return

        # 1. /api/users/self
        if path == "/api/users/self":
            self._send_json(200, self.state.users_self)
            return

        # 2. /api/userCertificates
        if path == "/api/userCertificates":
            self._send_json(200, self.state.user_certificates)
            return

        # 3. Sysinfo stat (/api/s/{site}/stat/sysinfo)
        m = re.match(r"^/api/s/([^/]+)/stat/sysinfo$", path)
        if m:
            sysinfo = [
                {
                    "version": "8.1.113",
                    "timezone": "UTC",
                    "hostname": "mock-udm-pro",
                    "ip_client": "192.168.1.100",
                    "uptime": 123456,
                }
            ]
            self._send_json(200, {"data": sysinfo})
            return

        # 4. /api/s/{site}/stat/{stat_type} (e.g. device, alluser)
        m = re.match(r"^/api/s/([^/]+)/stat/([^/]+)$", path)
        if m:
            site, stat_type = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, stat_type)
            self._send_json(200, {"data": store})
            return

        # 5. /api/s/{site}/get/setting or /api/s/{site}/get/setting/{key}
        m = re.match(r"^/api/s/([^/]+)/get/setting(?:/([^/]+))?$", path)
        if m:
            site, setting_key = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, "setting")
            if setting_key:
                filtered = [s for s in store if s.get("key") == setting_key]
                self._send_json(200, {"data": filtered})
            else:
                self._send_json(200, {"data": store})
            return

        # 6. v2 Policy endpoints GET
        m = re.match(r"^/v2/api/site/([^/]+)/(firewall/zone|firewall-policies|nat/rules|nat)$", path)
        if m:
            site, collection = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, collection)
            self._send_json(200, {"data": store})
            return

        # 7. Standard REST collection GET (/api/s/{site}/rest/{collection})
        m = re.match(r"^/api/s/([^/]+)/rest/([^/]+)$", path)
        if m:
            site, collection = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, collection)
            self._send_json(200, {"data": store})
            return

        self._send_json(404, {"meta": {"rc": "error", "msg": f"Endpoint {path} not found"}})

    # -----------------------------------------------------------------------
    # PUT Handlers
    # -----------------------------------------------------------------------
    def do_PUT(self) -> None:
        path = self._normalize_path(self.path)
        body = self._read_body() or {}
        self.state.requests_log.append({"method": "PUT", "path": path, "body": body})

        if not self._is_authenticated():
            self._send_unauthorized()
            return

        # 1. /api/userCertificates/{id}/status
        m = re.match(r"^/api/userCertificates/([^/]+)/status$", path)
        if m:
            cert_id = m.group(1)
            for cert in self.state.user_certificates:
                if cert.get("id") == cert_id:
                    cert["active"] = body.get("active", True)
                    self._send_json(200, cert)
                    return
            self._send_json(404, {"msg": f"Certificate {cert_id} not found"})
            return

        # 2. Setting PUT (/api/s/{site}/set/setting/{key}/{id} or /api/s/{site}/set/setting/{key})
        m = re.match(r"^/api/s/([^/]+)/set/setting/([^/]+)(?:/([^/]+))?$", path)
        if m:
            site, setting_key, setting_id = m.group(1), m.group(2), m.group(3)
            store = self.state.get_site_collection(site, "setting")
            target = None
            for s in store:
                if setting_id and s.get("_id") == setting_id:
                    target = s
                    break
                elif s.get("key") == setting_key:
                    target = s
                    break
            if not target:
                target = {"_id": f"set_{setting_key}_{uuid.uuid4().hex[:4]}", "key": setting_key}
                store.append(target)
            target.update(body)
            self._send_json(200, {"data": [target]})
            return

        # 3. User update (/api/s/{site}/rest/user/{id}) for DHCP reservations
        m = re.match(r"^/api/s/([^/]+)/rest/user/([^/]+)$", path)
        if m:
            site, user_id = m.group(1), m.group(2)
            store = self.state.get_site_collection(site, "alluser")
            for u in store:
                if u.get("_id") == user_id:
                    u.update(body)
                    self._send_json(200, {"data": [u]})
                    return
            self._send_json(404, {"msg": f"User {user_id} not found"})
            return

        # 4. v2 Policy PUT (/v2/api/site/{site}/{collection}/{id})
        m = re.match(r"^/v2/api/site/([^/]+)/(firewall/zone|firewall-policies|nat/rules|nat)/([^/]+)$", path)
        if m:
            site, collection, res_id = m.group(1), m.group(2), m.group(3)
            store = self.state.get_site_collection(site, collection)
            for item in store:
                if item.get("id") == res_id or item.get("_id") == res_id:
                    item.update(body)
                    self._send_json(200, {"data": [item]})
                    return
            self._send_json(404, {"msg": f"Item {res_id} not found"})
            return

        # 5. Standard REST PUT (/api/s/{site}/rest/{collection}/{id})
        m = re.match(r"^/api/s/([^/]+)/rest/([^/]+)/([^/]+)$", path)
        if m:
            site, collection, res_id = m.group(1), m.group(2), m.group(3)
            store = self.state.get_site_collection(site, collection)
            for item in store:
                if item.get("_id") == res_id or item.get("id") == res_id:
                    item.update(body)
                    self._send_json(200, {"data": [item]})
                    return
            self._send_json(404, {"msg": f"Item {res_id} not found in {collection}"})
            return

        self._send_json(404, {"meta": {"rc": "error", "msg": f"Endpoint {path} not found"}})

    # -----------------------------------------------------------------------
    # PATCH Handlers
    # -----------------------------------------------------------------------
    def do_PATCH(self) -> None:
        path = self._normalize_path(self.path)
        body = self._read_body() or {}
        self.state.requests_log.append({"method": "PATCH", "path": path, "body": body})

        if not self._is_authenticated():
            self._send_unauthorized()
            return

        if path == "/api/users/self":
            self.state.users_self.update(body)
            self._send_json(200, self.state.users_self)
            return

        self._send_json(404, {"meta": {"rc": "error", "msg": f"Endpoint {path} not found"}})

    # -----------------------------------------------------------------------
    # DELETE Handlers
    # -----------------------------------------------------------------------
    def do_DELETE(self) -> None:
        path = self._normalize_path(self.path)
        self.state.requests_log.append({"method": "DELETE", "path": path})

        if not self._is_authenticated():
            self._send_unauthorized()
            return

        # 1. /api/userCertificates/{id}
        m = re.match(r"^/api/userCertificates/([^/]+)$", path)
        if m:
            cert_id = m.group(1)
            self.state.user_certificates = [c for c in self.state.user_certificates if c.get("id") != cert_id]
            self._send_json(200, {})
            return

        # 2. v2 Policy DELETE (/v2/api/site/{site}/{collection}/{id})
        m = re.match(r"^/v2/api/site/([^/]+)/(firewall/zone|firewall-policies|nat/rules|nat)/([^/]+)$", path)
        if m:
            site, collection, res_id = m.group(1), m.group(2), m.group(3)
            store = self.state.get_site_collection(site, collection)
            self.state.sites[site][collection] = [
                item for item in store if item.get("id") != res_id and item.get("_id") != res_id
            ]
            self._send_json(200, {"data": []})
            return

        # 3. Standard REST DELETE (/api/s/{site}/rest/{collection}/{id})
        m = re.match(r"^/api/s/([^/]+)/rest/([^/]+)/([^/]+)$", path)
        if m:
            site, collection, res_id = m.group(1), m.group(2), m.group(3)
            store = self.state.get_site_collection(site, collection)
            self.state.sites[site][collection] = [
                item for item in store if item.get("_id") != res_id and item.get("id") != res_id
            ]
            self._send_json(200, {"data": []})
            return

        self._send_json(404, {"meta": {"rc": "error", "msg": f"Endpoint {path} not found"}})


class MockUniFiServer:
    """Convenient wrapper running MockUniFiRequestHandler in a background daemon thread."""

    def __init__(self) -> None:
        self.state = MockUniFiState()

        # Subclass handler to bind the specific state instance
        state_instance = self.state

        class BoundHandler(MockUniFiRequestHandler):
            state = state_instance

        self._server = HTTPServer(("127.0.0.1", 0), BoundHandler)
        self.port = self._server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def reset(self) -> None:
        self.state.reset()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
