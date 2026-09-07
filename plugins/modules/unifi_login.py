#!/usr/bin/python
# (c) 2026, Olof Hellqvist (@hellqvio86)
# MIT License (see LICENSE.md)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: unifi_login
short_description: Authenticate with a UniFi controller and return a reusable session
version_added: "0.0.32"
description:
    - Authenticate against a UniFi controller and retrieve pre-authenticated session tokens.
    - Returns C(session_cookie) and C(csrf_token) that can be registered and reused across subsequent
      tasks or playbooks via C(module_defaults) using C(unifi_session_cookie) and C(unifi_csrf_token).
    - Prevents repeating login authentication handshakes across multiple module invocations.
    - Also discovers and returns available sites on the controller.
options:
    host:
        description: The host or IP address of the UniFi controller.
        required: true
        type: str
    username:
        description: UniFi controller administrator username.
        required: true
        type: str
    password:
        description: UniFi controller administrator password.
        required: true
        type: str
    site:
        description: Target UniFi site name.
        default: default
        type: str
    validate_certs:
        description: Verify SSL certificates.
        default: true
        type: bool
    ca_path:
        description: Path to CA bundle file for TLS verification.
        required: false
        type: path
author:
    - Olof Hellqvist (@hellqvio86)
"""

EXAMPLES = r"""
- name: Log in to UniFi controller
  hellqvio86.unifi.unifi_login:
    host: "192.168.1.1"
    username: "admin"
    password: "{{ unifi_password }}"
  register: auth

- name: Perform operations using reused session
  module_defaults:
    group/hellqvio86.unifi.unifi:
      host: "192.168.1.1"
      unifi_session_cookie: "{{ auth.unifi_session.session_cookie }}"
      unifi_csrf_token: "{{ auth.unifi_session.csrf_token }}"
      site: "{{ auth.unifi_session.site }}"
  block:
    - name: Ensure WiFi SSID exists
      hellqvio86.unifi.unifi_wlan:
        name: "GuestWiFi"
        state: present
"""

RETURN = r"""
changed:
    description: Always false since login does not mutate controller configuration.
    type: bool
    returned: always
unifi_session:
    description: Reusable session tokens and controller metadata.
    type: dict
    returned: always
    contains:
        session_cookie:
            description: Pre-authenticated session cookie string.
            type: str
        csrf_token:
            description: Pre-authenticated CSRF token.
            type: str
        site:
            description: Target site identifier.
            type: str
        host:
            description: Controller host address.
            type: str
        sites:
            description: List of available sites discovered on the controller.
            type: list
            elements: dict
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.hellqvio86.unifi.plugins.module_utils.unifi_api import UnifiAPI


def run_module() -> None:
    """Execute unifi_login module logic."""
    module_args: dict[str, Any] = dict(
        host=dict(type="str", required=True),
        username=dict(type="str", required=True, no_log=True),
        password=dict(type="str", required=True, no_log=True),
        site=dict(type="str", default="default"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="path", required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    host: str = module.params["host"]
    site: str = module.params["site"]

    if module.check_mode:
        module.exit_json(
            changed=False,
            unifi_session={
                "session_cookie": "check-mode-cookie",
                "csrf_token": "check-mode-csrf",
                "site": site,
                "host": host,
                "sites": [{"name": site, "desc": site}],
            },
        )
        return

    api = UnifiAPI(
        module,
        host=host,
        username=module.params["username"],
        password=module.params["password"],
        validate_certs=module.params["validate_certs"],
        ca_path=module.params.get("ca_path"),
    )

    success = api.login()
    if not success:
        module.fail_json(msg="UniFi login failed to authenticate")
        return

    session_cookie = api.session_cookie or ""
    csrf_token = api.csrf_token or ""

    # Discover available sites on the controller
    discovered_sites: list[dict[str, Any]] = []
    res, info = api.request("/proxy/network/api/self/sites")
    if res is None and info.get("status") == 404:
        res, info = api.request("/api/self/sites")

    if isinstance(res, dict) and "data" in res and isinstance(res["data"], list):
        for s in res["data"]:
            if isinstance(s, dict):
                discovered_sites.append(
                    {
                        "name": s.get("name"),
                        "desc": s.get("desc") or s.get("name"),
                        "role": s.get("role"),
                    }
                )
    elif isinstance(res, list):
        for s in res:
            if isinstance(s, dict):
                discovered_sites.append(
                    {
                        "name": s.get("name"),
                        "desc": s.get("desc") or s.get("name"),
                        "role": s.get("role"),
                    }
                )

    module.exit_json(
        changed=False,
        unifi_session={
            "session_cookie": session_cookie,
            "csrf_token": csrf_token,
            "site": site,
            "host": host,
            "sites": discovered_sites,
        },
    )


def main() -> None:
    """Entry point for unifi_login."""
    run_module()


if __name__ == "__main__":
    main()
