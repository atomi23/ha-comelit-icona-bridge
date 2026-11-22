[Deutsch](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) | **English**

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) · [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md) · [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md) · [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md) · [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

# Companion (HACS)

After [installation step 3](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) you get:

| Entity (example) | Role |
|---|---|
| `camera.comelit_icona_bridge_klingelkamera` | Live RTSP (calls `/start` on stream); stills grab a frame while video is active, otherwise return the last cached frame |
| `button.*_start_klingelvideo` / `*_stop_klingelvideo` | `POST /start` / `/stop` |
| `button.*_klingel_annehmen_sprechen` | `POST /answer` |
| `button.*_tur_offnen` | `POST /door` |
| `binary_sensor.*_klingelt` | `/status.ringing` |
| `binary_sensor.*_icona_verbindung` | `/status.connected` |
| `event.*_klingel` | ring / answered / door / video |

HA startup does not start video. The still cache is memory-only and empty after an HA restart. Companion buttons show an HA error if the bridge call fails.

Manual copy into `config/custom_components/` still works if you prefer not to use HACS.
