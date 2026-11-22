**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# Add-on-Optionen

| Option | Bedeutung |
|--------|---------|
| `host` | IP-Adresse der Sprechanlage |
| `port` | `64100` |
| `token` | **Beim 6741W erforderlich** — ICONA-Benutzertoken aus 32 Hex-Zeichen |
| `password` | **Optional.** Beim 6741W-Zugang als Installer/Hausverwalter leer lassen (keine Backup-Schaltfläche). Nur für andere Modelle mit Web-Backup. |
| `enable_vip_listener` | CTPP für Klingelereignisse offen halten (Standard true) |
| `auto_start_on_ring` | Bei Klingeln eingehendes Video starten (Standard true) |
| `model` | `6741W` |

### Steuerungs-API

- `GET /status` — Verbindung, VIP, Video, Klingeln, Medienzähler
- `GET /events` — letzte Klingel-/Annehmen-/Tür-/Videoereignisse
- `POST /start` — ausgehende Live-Ansicht
- `POST /stop` — Video beenden
- `POST /answer` — Annehmen / Sprechen (eingehend)
- `POST /door?name=Schloss` — Tür öffnen
