# ha-comelit-icona-bridge

Home Assistant **add-on** that opens a local **ICONA / VIPER** session to a Comelit WiFi video door panel (**6741W** / 6701W family, TCP **64100**) and republishes the outdoor doorbell camera as **RTSP on the HA host** (`rtsp://<ha-ip>:8557/intercom`) for Lovelace / go2rtc / Generic Camera.

Companion HACS integration: camera + start/stop/answer/door buttons + ringing sensor.

No cloud auth bypass. No Frida. No LAN packet-capture required — the add-on speaks ICONA itself.

## Quickstart (3 steps)

1. **Add the add-on repo** — HA → **Settings → Add-ons → Add-on store → ⋮ → Repositories** → add  
   `https://github.com/atomi23/ha-comelit-icona-bridge`  
   Install **Comelit ICONA Bridge** (local Docker build).

2. **Set host + token** — Options: panel IP (`host`) and the 32-hex ICONA `token`. Leave **`password` empty** (optional; only useful on models with a web Backup UI — not on typical 6741W Installer/Hausverwalter). Start the add-on. Check `http://<ha-ip>:8099/status`.

3. **Install the HACS companion** — HACS → Integrations → ⋮ → Custom repositories → same GitHub URL, category **Integration** → download **Comelit ICONA Bridge Camera** → restart HA → add the integration. URLs are auto-detected when the add-on is running (`rtsp://127.0.0.1:8557/intercom`, `http://homeassistant.local:8099`).

Optional: paste the go2rtc snippet from [`docs/go2rtc-comelit-icona.yaml`](docs/go2rtc-comelit-icona.yaml) and import [`dashboards/kuechen-panel-example.yaml`](dashboards/kuechen-panel-example.yaml) (`camera_view: auto`, not live).

Hourly still preview without lasting outdoor LEDs (PN-32): install [`packages/hourly_klingel_preview.yaml`](packages/hourly_klingel_preview.yaml) via `homeassistant.packages` **or** the blueprint under [`blueprints/automation/comelit_icona_bridge/`](blueprints/automation/comelit_icona_bridge/) — see [`docs/hourly-preview.md`](docs/hourly-preview.md). Browser talk needs HTTPS: [`docs/https-mic.md`](docs/https-mic.md).

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

## Add-on options

| Option | Meaning |
|--------|---------|
| `host` | Panel IP |
| `port` | `64100` |
| `token` | **Required on 6741W** — 32-hex ICONA user-token |
| `password` | **Optional.** Leave empty on 6741W Installer/Hausverwalter (no Backup button). Only for other models that expose web backup. |
| `enable_vip_listener` | Keep CTPP open for doorbell rings (default true) |
| `auto_start_on_ring` | Start inbound video on ring (default true) |
| `model` | `6741W` |

### Control API

- `GET /status` — connection, VIP, video, ring, media counters
- `GET /events` — recent ring/answer/door/video events
- `POST /start` — outbound live view
- `POST /stop` — end video
- `POST /answer` — answer / talk path (inbound)
- `POST /door?name=Schloss` — open door

## Companion (HACS)

After step 3 above you get:

| Entity (example) | Role |
|---|---|
| `camera.comelit_icona_bridge_klingelkamera` | Live RTSP (calls `/start` on stream) |
| `button.*_start_klingelvideo` / `*_stop_klingelvideo` | `POST /start` / `/stop` |
| `button.*_klingel_annehmen_sprechen` | `POST /answer` |
| `button.*_tur_offnen` | `POST /door` |
| `binary_sensor.*_klingelt` | `/status.ringing` |
| `binary_sensor.*_icona_verbindung` | `/status.connected` |
| `event.*_klingel` | ring / answered / door / video |

Manual copy into `config/custom_components/` still works if you prefer not to use HACS.

## Sample dashboard & go2rtc

- Lovelace example (still `camera_view: auto` + Start/Stop + ringing): [`dashboards/kuechen-panel-example.yaml`](dashboards/kuechen-panel-example.yaml)
- One-paste go2rtc stream: [`docs/go2rtc-comelit-icona.yaml`](docs/go2rtc-comelit-icona.yaml)
- Hourly preview package / blueprint (short LED blink): [`docs/hourly-preview.md`](docs/hourly-preview.md)
- HTTPS for browser mic + `http:` migration repair: [`docs/https-mic.md`](docs/https-mic.md)

```yaml
streams:
  comelit_icona:
    - rtsp://127.0.0.1:8557/intercom
```

### Install hourly preview package

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

Copy [`packages/hourly_klingel_preview.yaml`](packages/hourly_klingel_preview.yaml) into `config/packages/`, ensure `/media/comelit_icona/` exists, reload automations. Or import the blueprint from [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml). Expect a **brief outdoor LED blink** once per hour during start→snapshot→stop.

## Attribution

Maintained by [atomi23](https://github.com/atomi23).

ICONA protocol client, CTPP/video call, VIP listener, RTP receiver and local RTSP server are **adapted from** [`mnestrud/comelit-man`](https://github.com/mnestrud/comelit-man) (Apache-2.0; see `NOTICE` / `LICENSE`).

## License

Apache License 2.0
