[Deutsch](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/README.md) | **English**

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) · [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md) · [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md) · [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md) · [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

# ha-comelit-icona-bridge

Home Assistant **add-on** that opens a local **ICONA / VIPER** session to a Comelit WiFi video door panel (**6741W** / 6701W family, TCP **64100**) and republishes the outdoor doorbell camera as **RTSP on the HA host** (`rtsp://<ha-ip>:8557/intercom`) for Lovelace / go2rtc / Generic Camera.

Companion HACS integration: camera + start/stop/answer/door buttons + ringing sensor.

No cloud auth bypass. No Frida. No LAN packet-capture required — the add-on speaks ICONA itself.

## Quickstart (3 steps)

1. **Add the add-on repo** — HA → **Settings → Add-ons → Add-on store → ⋮ → Repositories** → add\
   `https://github.com/atomi23/ha-comelit-icona-bridge`\
   Install **Comelit ICONA Bridge** (local Docker build).

2. **Set host + token** — Options: panel IP (`host`) and the 32-hex ICONA `token`. Leave **`password` empty** (optional; only useful on models with a web Backup UI — not on typical 6741W Installer/Hausverwalter). Start the add-on. Check `http://<ha-ip>:8099/status`.

3. **Install the HACS companion** — HACS → Integrations → ⋮ → Custom repositories → same GitHub URL, category **Integration** → download **Comelit ICONA Bridge Camera** → restart HA → add the integration. Discovery probes the API only on port `8099`. The suggested RTSP URL uses the discovered host (recognized local aliases use `127.0.0.1`) and the valid `rtsp_port` reported by `/status` (fallback `8557`). With a custom `api_port`, enter both URLs manually.

## Page index

- [Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md)
- [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md)
- [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md)
- [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md)
- [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md)
- [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

## Where to buy

- [Search Amazon.de for Comelit 6741W (Prime filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6741W&rh=p_85%3A20943776031)\*
- [Search Amazon.de for Comelit 6701W (Prime filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6701W&rh=p_85%3A20943776031)\*

### Accessories

- [Search Amazon.de for Home Assistant Green for the HA host (Prime filter)](https://www.amazon.de/s?tag=atomi23-21&k=Home+Assistant+Green&rh=p_85%3A20943776031)\*
- [Search Amazon.de for an Android tablet for the kitchen dashboard (Prime filter)](https://www.amazon.de/s?tag=atomi23-21&k=Android+Tablet&rh=p_85%3A20943776031)\*
- [Search Amazon.de for a tablet wall mount for the kitchen dashboard (Prime filter)](https://www.amazon.de/s?tag=atomi23-21&k=Tablet+Wandhalterung&rh=p_85%3A20943776031)\*

\*As an Amazon Associate I earn from qualifying purchases. Links marked * are affiliate/advertising links.
