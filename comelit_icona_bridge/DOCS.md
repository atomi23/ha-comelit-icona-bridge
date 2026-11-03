# Comelit ICONA Bridge (Add-on)

Local-only bridge for Comelit **6741W** / 6701W-family panels: ICONA TCP `:64100` → RTSP on the HA host (`:8557/intercom`) plus HTTP control on `:8099`.

## Quickstart (3 steps)

1. **Add repo** — Add-on store → ⋮ → Repositories → `https://github.com/atomi23/ha-comelit-icona-bridge` → install **Comelit ICONA Bridge**.
2. **host + token** — Set panel IP and ICONA `token`. Leave **`password` empty** (optional field; not used on typical 6741W Installer/Hausverwalter UIs without Backup). Start the add-on; confirm `GET http://<ha-ip>:8099/status`.
3. **HACS companion** — HACS custom repository (same URL, category **Integration**) → install **Comelit ICONA Bridge Camera** → restart → add integration (URLs auto-detect when the add-on is up).

Sample Lovelace view: `dashboards/kuechen-panel-example.yaml` in the repo (`camera_view: auto`, Start/Stop tiles). go2rtc one-liner: `docs/go2rtc-comelit-icona.yaml`.

Hourly still without lasting outdoor LEDs: `packages/hourly_klingel_preview.yaml` (HA `packages:`) or `blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml` — see `docs/hourly-preview.md`. Browser mic / HTTPS: `docs/https-mic.md`.

## Credentials (6741W)

Set **`token`** (32-hex ICONA user-token). Leave **`password` empty**.

On 6741W panels where **Installer** / **Hausverwalter** web logins on `:8080` have **no Backup button**, add-on password→backup→`users.cfg` extraction **does not work**. Reuse an existing ICONA token (HA config entry / previously saved token).

The `password` option is **optional** in the schema and remains only for other Comelit models that expose configuration backup in the web UI.

## Options

| Option | Meaning |
|--------|---------|
| `host` | Comelit panel IP |
| `port` | ICONA port (default `64100`) |
| `http_port` | Device web UI (default `8080`) — not used for token on typical 6741W |
| `token` | **Required on 6741W.** 32-char hex ICONA `user-token` |
| `password` | **Optional.** Leave empty on 6741W without backup UI |
| `rtsp_port` / `api_port` | Local RTSP / control API (defaults `8557` / `8099`) |
| `enable_vip_listener` | Persistent CTPP VIP listener for doorbell rings |
| `auto_start_on_ring` | Auto start inbound video when the panel rings |
| `model` | Device label (default `6741W`) |

## Control API

- `GET /status` — connection / VIP / video / ring / media counters
- `GET /events` — recent doorbell and call events
- `POST /start` — outbound live video → RTSP
- `POST /stop` — end video session
- `POST /answer` — answer / talk (inbound audio TX via RTSP backchannel)
- `POST /door?name=Schloss` — open door / relay

## Stream URL

```text
rtsp://<HA-LAN-IP>:8557/intercom
```

On the same HA host (companion / go2rtc): `rtsp://127.0.0.1:8557/intercom`.

Only one ICONA video client at a time. Prefer the HA OS add-on with `host_network` for RTP media (UDP return path).

## go2rtc (one paste)

In the AlexxIT go2rtc add-on config (or `go2rtc.yaml`):

```yaml
streams:
  comelit_icona:
    - rtsp://127.0.0.1:8557/intercom
```

Full snippet file in the repo: `docs/go2rtc-comelit-icona.yaml`.

## Ring / talk / camera

1. Add-on starts → auth + VIP listener (`vip_listener: true` in `/status`)
2. Doorbell ring → `/events` shows `ring`; companion `event.*klingel` + `binary_sensor.*klingelt`
3. Live camera → `/start` or auto-on-ring → `rtsp://…:8557/intercom` (go2rtc / Lovelace)
4. Talk → `/answer` after ring (browser mic needs HTTPS origin — see `docs/https-mic.md`); RX audio works over go2rtc WebRTC

## Hourly preview (short LED window)

Do not leave Lovelace on `camera_view: live` for a kitchen still. Use `auto` plus the hourly package/blueprint: Start → short wait → `camera.snapshot` to `/media` → Stop. Outdoor LEDs may blink briefly each hour; that is expected.
