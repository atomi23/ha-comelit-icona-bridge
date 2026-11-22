[Deutsch](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) | **English**

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) · [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md) · [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md) · [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md) · [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

# Add-on options

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
