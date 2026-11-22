**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# Begleitintegration (HACS)

Nach [Schritt 3 der Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) stehen folgende Entitäten zur Verfügung:

| Entität (Beispiel) | Aufgabe |
|---|---|
| `camera.comelit_icona_bridge_klingelkamera` | Live-RTSP (ruft beim Streamen `/start` auf); Standbilder werden bei aktivem Video erfasst, sonst wird das zuletzt zwischengespeicherte Bild zurückgegeben |
| `button.*_start_klingelvideo` / `*_stop_klingelvideo` | `POST /start` / `/stop` |
| `button.*_klingel_annehmen_sprechen` | `POST /answer` |
| `button.*_tur_offnen` | `POST /door` |
| `binary_sensor.*_klingelt` | `/status.ringing` |
| `binary_sensor.*_icona_verbindung` | `/status.connected` |
| `event.*_klingel` | Klingeln / angenommen / Tür / Video |

Der HA-Start startet kein Video. Der Standbild-Zwischenspeicher liegt nur im Arbeitsspeicher und ist nach einem HA-Neustart leer. Die Tasten der Begleitintegration zeigen einen HA-Fehler an, wenn der Aufruf der Bridge fehlschlägt.

Manuelles Kopieren nach `config/custom_components/` funktioniert weiterhin, falls du HACS nicht verwenden möchtest.
