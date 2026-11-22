**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# Installation

## Schnellstart (3 Schritte)

1. **Add-on-Repository hinzufügen** — HA → **Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories** → hinzufügen:\
   `https://github.com/atomi23/ha-comelit-icona-bridge`\
   **Comelit ICONA Bridge** installieren (lokaler Docker-Build).

2. **Host + Token festlegen** — Optionen: IP-Adresse der Sprechanlage (`host`) und das ICONA-`token` aus 32 Hex-Zeichen. **`password` leer lassen** (optional; nur bei Modellen mit einer Web-Backup-Oberfläche sinnvoll — nicht beim üblichen 6741W-Zugang als Installer/Hausverwalter). Add-on starten. `http://<ha-ip>:8099/status` prüfen.

3. **HACS-Begleitintegration installieren** — HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → dieselbe GitHub-URL, Kategorie **Integration** → **Comelit ICONA Bridge Camera** herunterladen → HA neu starten → Integration hinzufügen. Die Erkennung prüft die API nur auf Port `8099`. Die vorgeschlagene RTSP-URL verwendet den erkannten Host (erkannte lokale Aliasnamen verwenden `127.0.0.1`) und den gültigen, von `/status` gemeldeten `rtsp_port` (Rückfallwert `8557`). Bei einem eigenen `api_port` beide URLs manuell eingeben.

Optional: das go2rtc-Beispiel aus [`docs/go2rtc-comelit-icona.yaml`](../docs/go2rtc-comelit-icona.yaml) einfügen und [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml) importieren (`camera_view: auto`, nicht live).

Stündliches Standbild ohne dauerhaft leuchtende Außen-LEDs (PN-32): [`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) über `homeassistant.packages` **oder** die Blaupause unter [`blueprints/automation/comelit_icona_bridge/`](../blueprints/automation/comelit_icona_bridge/) installieren — siehe [`docs/hourly-preview.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md). Sprechen im Browser benötigt HTTPS: [`docs/https-mic.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md).

## Status des 6741W

In der Praxis mit Comelit **6741W** getestet:

| Funktion | Status |
|---|---|
| UAUT-Authentifizierung + UCFG-Konfiguration | Funktioniert |
| VIP-CTPP-Listener (Klingelereignisse) | Funktioniert (Add-on hält CTPP offen) |
| Signalisierung ausgehender Live-Videositzungen (CTPP/UDPM/RTPC) | Funktioniert |
| RTP → lokale RTSP-Medien | Add-on mit **host_network** unter HA OS ausführen |
| Annehmen / Sprechen | `POST /answer` → eingehenden Anruf annehmen + RTSP-Rückkanal (Mikrofon benötigt HTTPS im Browser) |
| Tür öffnen | `POST /door` (Schloss / Relais) |

## Danksagung

Gepflegt von [atomi23](https://github.com/atomi23).

ICONA-Protokollclient, CTPP-/Videoanruf, VIP-Listener, RTP-Empfänger und lokaler RTSP-Server sind **angepasste Versionen aus** [`mnestrud/comelit-man`](https://github.com/mnestrud/comelit-man) (Apache-2.0; siehe `NOTICE` / `LICENSE`).

## Lizenz

Apache License 2.0
