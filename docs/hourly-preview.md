**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# Stündliche Klingel-Vorschau (PN-32)

Ziel: ein aktuelles **Standbild** der Außenkamera auf einem Küchen-/Panel-Dashboard anzeigen, **ohne** ICONA-Live-Video (und die Außen-LEDs) dauerhaft eingeschaltet zu lassen.

## Warum nicht `camera_view: live`?

`picture-entity` mit `camera_view: live` öffnet den RTSP-Pfad und ruft normalerweise `/start` auf, wodurch die Außen-LEDs der Sprechanlage eingeschaltet werden können. Jede ICONA-Videositzung endet nach 120 s; anschließend wird der Klingel-Listener fortgesetzt, sofern er aktiviert und verbunden ist. Für Standbilder **`camera_view: auto`** verwenden. Die Start-/Stop-Kacheln zur bedarfsgesteuerten Videosteuerung beibehalten.

Der HA-Start startet kein Video. Die Begleitintegration erfasst bei aktivem Video ein Standbild; andernfalls gibt sie das zuletzt zwischengespeicherte Bild zurück. Dieser Zwischenspeicher liegt nur im Arbeitsspeicher, ist nach einem HA-Neustart leer und wird nicht aus der gespeicherten JPEG-Datei wiederhergestellt.

## Paket oder Blaupause

| Pfad | Aufgabe |
|------|------|
| [`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) | Direkt verwendbares HA-**Paket** (Automation) |
| [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](../blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml) | Gleicher Ablauf als **Blaupause** (Eingaben über die Oberfläche) |
| [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml) | Lovelace-Beispiel: `camera_view: auto` + Start/Stop |

### Installation über `packages:`

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

`packages/hourly_klingel_preview.yaml` nach `config/packages/` kopieren, `/media/comelit_icona/` anlegen und neu starten (oder Automationen neu laden).

### Installation über die Blaupause

Die Blaupausendatei nach `config/blueprints/automation/comelit_icona_bridge/` kopieren, `/media/comelit_icona/` anlegen (wie beim Paket), dann unter **Einstellungen → Automationen & Szenen → Automation erstellen** die Blaupause **ICONA hourly Klingel preview** auswählen.

## LED-Verhalten

Jeder stündliche Durchlauf: **Start** → ca. 4 s warten → **Standbild** → **Stop**. Die IR-/Weißlicht-LEDs außen können einmal pro Stunde **kurz aufleuchten**. Das ist zu erwarten. Leuchten sie zu lange, die Wartezeit verkürzen (Eingabe der Blaupause / Verzögerung im Paket bearbeiten); bei schwarzen Standbildern leicht erhöhen (z. B. auf 5–6 s).

Paket und Blaupause verwenden bei `camera.snapshot` die Einstellung `continue_on_error: true`, damit Stop auch nach einem fehlgeschlagenen Standbild ausgeführt wird. Die Tasten der Begleitintegration zeigen einen HA-Fehler an, wenn der Aufruf der Bridge fehlschlägt.

## Optionales go2rtc-Standbild

Wenn AlexxIT go2rtc bereits mit `comelit_icona` läuft (siehe [`go2rtc-comelit-icona.yaml`](go2rtc-comelit-icona.yaml)), lässt sich nach `/start` statt `camera.snapshot` eine JPEG-Datei über die Frame-API von go2rtc abrufen. Die Kommentare im Paket zeigen die Austauschstelle. Das aktualisiert nur die Datei, nicht das zwischengespeicherte Standbild der Begleitkamera; zur Anzeige eine Medien-/Datei-Bildkarte verwenden (siehe auskommentiertes Beispiel in `dashboards/kuechen-panel-example.yaml`). Weiterhin umgehend **Stop** ausführen, damit die LEDs ausgehen.
