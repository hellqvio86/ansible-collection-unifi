# hellqvio86.unifi.unifi_dhcp_reservation

Manage DHCP fixed IP reservations on a UniFi controller.

## Description

Create, update, or delete DHCP fixed IP (static) reservations for known client devices. The client must already be known to the UniFi controller (must have connected at least once).

Typically used in a loop over a list of desired reservations (see intent-based example below). When used with session reuse parameters, all loop iterations share a single authentication session to avoid UniFi rate limits.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `mac` | str | Yes | | MAC address of the client device. |
| `state` | str | No | `present` | Whether the reservation should be `present` or `absent`. |
| `fixed_ip` | str | Yes (if present) | | Static IP address to assign. Required when `state=present`. |
| `name` | str | No | | Friendly name to assign to the client. |
| `network_name` | str | No | | Name of the network (LAN) for the reservation. |
| `unifi_session_cookie` | str | No | | Reuse an existing UniFi session cookie to avoid repeated logins. |
| `unifi_csrf_token` | str | No | | CSRF token corresponding to the session cookie. |

## Examples

### Create a single reservation
```yaml
- name: Ensure Example Device has a static IP
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:01"
    name: "Example Device"
    fixed_ip: "198.51.100.71"
    network_name: "Default"
    state: present
```

### Remove a DHCP reservation
```yaml
- name: Remove static IP from a device
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    username: "admin"
    password: "password"
    mac: "02:1a:2b:3c:4d:02"
    state: absent
```

### Intent-based loop with session reuse
```yaml
- name: Authenticate once
  ansible.builtin.uri:
    url: "https://{{ host }}/api/auth/login"
    method: POST
    body_format: json
    body:
      username: "{{ username }}"
      password: "{{ password }}"
    validate_certs: false
    status_code: 200
  register: _login

- name: Set session facts
  ansible.builtin.set_fact:
    unifi_session_cookie: "{{ _login.cookies_string }}"
    unifi_csrf_token: >-
      {% set b64 = _login.cookies.TOKEN.split('.')[1] %}
      {% set pad = '=' * ((4 - b64 | length % 4) % 4) %}
      {{ (b64 ~ pad) | b64decode | from_json | json_query('csrfToken') }}

- name: Apply all DHCP reservations
  hellqvio86.unifi.unifi_dhcp_reservation:
    host: "192.0.2.1"
    mac: "{{ item.mac }}"
    name: "{{ item.name | default(omit) }}"
    fixed_ip: "{{ item.ip }}"
    network_name: "{{ item.network | default(omit) }}"
    state: "{{ item.state | default('present') }}"
    unifi_session_cookie: "{{ unifi_session_cookie }}"
    unifi_csrf_token: "{{ unifi_csrf_token }}"
  loop: "{{ dhcp_reservations }}"
```

## Return Values

| Key | Type | Description |
|-----|------|-------------|
| `changed` | bool | Whether any change was applied. |
| `reservation` | dict | Current reservation state (when state=present and client is found). |
| `client` | dict | Current client state (when client is found). |
