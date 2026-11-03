# Browser talk (mic) over HTTPS

Outbound talk (`POST /answer` / **Sprechen**) needs a **secure origin** in the browser.
HTTP `http://homeassistant.local:8123` often cannot use the microphone.

## Preferred paths

1. **NGINX Home Assistant SSL Proxy** (add-on)  
   Terminate TLS on the proxy; open HA via `https://…`. Use this when you already have a certificate or want a reverse proxy in front of HA.

2. **DuckDNS + Let’s Encrypt**  
   DuckDNS add-on (or similar) for a hostname + Let’s Encrypt certificate, then reach HA at `https://<your-duckdns>.duckdns.org:8123` (or via NGINX SSL Proxy with those certs).

After HTTPS works, open the Lovelace view from that HTTPS URL and use **Sprechen**. Camera stills / Start / Stop do not require the mic.

## Repair: leftover `http:` after UI migration

If Settings shows something like **`yaml_still_present_after_migration`** (or network settings refuse to save) after moving HTTP/network config into the UI:

1. Open `configuration.yaml`.
2. **Remove** any leftover top-level `http:` block that duplicates what the UI now owns (e.g. `ssl_certificate`, `ssl_key`, `server_port`, `use_x_forwarded_for`, `trusted_proxies` only if you migrated those to the UI / proxy add-on).
3. Keep proxy-related keys only where your chosen path needs them (often in the NGINX SSL Proxy add-on config, not in core `http:`).
4. Check configuration → restart Home Assistant.

Do not delete unrelated YAML. Only clear the migrated `http:` leftovers the repair message refers to.
