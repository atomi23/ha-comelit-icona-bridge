[Deutsch](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) | **English**

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) · [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md) · [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md) · [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md) · [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

# Installation

## Quickstart (3 steps)

1. **Add the add-on repo** — HA → **Settings → Add-ons → Add-on store → ⋮ → Repositories** → add\
   `https://github.com/atomi23/ha-comelit-icona-bridge`\
   Install **Comelit ICONA Bridge** (local Docker build).

2. **Set host + token** — Options: panel IP (`host`) and the 32-hex ICONA `token`. Leave **`password` empty** (optional; only useful on models with a web Backup UI — not on typical 6741W Installer/Hausverwalter). Start the add-on. Check `http://<ha-ip>:8099/status`.

3. **Install the HACS companion** — HACS → Integrations → ⋮ → Custom repositories → same GitHub URL, category **Integration** → download **Comelit ICONA Bridge Camera** → restart HA → add the integration. Discovery probes the API only on port `8099`. The suggested RTSP URL uses the discovered host (recognized local aliases use `127.0.0.1`) and the valid `rtsp_port` reported by `/status` (fallback `8557`). With a custom `api_port`, enter both URLs manually.

Optional: paste the go2rtc snippet from [`docs/go2rtc-comelit-icona.yaml`](../docs/go2rtc-comelit-icona.yaml) and import [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml) (`camera_view: auto`, not live).

Hourly still preview without lasting outdoor LEDs (PN-32): install [`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) via `homeassistant.packages` **or** the blueprint under [`blueprints/automation/comelit_icona_bridge/`](../blueprints/automation/comelit_icona_bridge/) — see [`docs/hourly-preview.en.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md). Browser talk needs HTTPS: [`docs/https-mic.en.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md).

## 6741W status

Field-tested on Comelit **6741W**:

| Capability | Status |
|---|---|
| UAUT auth + UCFG config | Working |
| VIP CTPP listener (doorbell ring events) | Working (add-on keeps CTPP open) |
| Outbound live video signaling (CTPP/UDPM/RTPC) | Working |
| RTP → local RTSP media | Run add-on with **host_network** on HA OS |
| Answer / talk | `POST /answer` → inbound answer + RTSP backchannel (mic needs HTTPS in browser) |
| Door open | `POST /door` (Schloss / Relais) |

## Attribution

Maintained by [atomi23](https://github.com/atomi23).

ICONA protocol client, CTPP/video call, VIP listener, RTP receiver and local RTSP server are **adapted from** [`mnestrud/comelit-man`](https://github.com/mnestrud/comelit-man) (Apache-2.0; see `NOTICE` / `LICENSE`).

## License

Apache License 2.0
