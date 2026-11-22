[English](README.md) | Deutsch

# ha-comelit-icona-bridge

Home-Assistant-**Add-on**, das eine lokale **ICONA-/VIPER**-Sitzung zu einer Comelit-WLAN-Videosprechanlage (**6741W** / 6701W-Familie, TCP **64100**) öffnet und die Außenkamera als **RTSP auf dem HA-Host** (`rtsp://<ha-ip>:8557/intercom`) für Lovelace / go2rtc / Generic Camera bereitstellt.

Begleitende HACS-Integration: Kamera + Start-/Stop-/Annehmen-/Tür-Tasten + Klingelsensor.

Keine Umgehung der Cloud-Authentifizierung. Kein Frida. Kein Mitschneiden von LAN-Paketen nötig — das Add-on spricht selbst ICONA.

## Schnellstart (3 Schritte)

1. **Add-on-Repository hinzufügen** — HA → **Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories** → hinzufügen:  
   `https://github.com/atomi23/ha-comelit-icona-bridge`  
   **Comelit ICONA Bridge** installieren (lokaler Docker-Build).

2. **Host + Token festlegen** — Optionen: IP-Adresse der Sprechanlage (`host`) und das ICONA-`token` aus 32 Hex-Zeichen. **`password` leer lassen** (optional; nur bei Modellen mit einer Web-Backup-Oberfläche sinnvoll — nicht beim üblichen 6741W-Zugang als Installer/Hausverwalter). Add-on starten. `http://<ha-ip>:8099/status` prüfen.

3. **HACS-Begleitintegration installieren** — HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → dieselbe GitHub-URL, Kategorie **Integration** → **Comelit ICONA Bridge Camera** herunterladen → HA neu starten → Integration hinzufügen. Die Erkennung prüft die API nur auf Port `8099`. Die vorgeschlagene RTSP-URL verwendet den erkannten Host (erkannte lokale Aliasnamen verwenden `127.0.0.1`) und den gültigen, von `/status` gemeldeten `rtsp_port` (Rückfallwert `8557`). Bei einem eigenen `api_port` beide URLs manuell eingeben.

Optional: das go2rtc-Beispiel aus [`docs/go2rtc-comelit-icona.yaml`](docs/go2rtc-comelit-icona.yaml) einfügen und [`dashboards/kuechen-panel-example.yaml`](dashboards/kuechen-panel-example.yaml) importieren (`camera_view: auto`, nicht live).

Stündliches Standbild ohne dauerhaft leuchtende Außen-LEDs (PN-32): [`packages/hourly_klingel_preview.yaml`](packages/hourly_klingel_preview.yaml) über `homeassistant.packages` **oder** die Blaupause unter [`blueprints/automation/comelit_icona_bridge/`](blueprints/automation/comelit_icona_bridge/) installieren — siehe [`docs/hourly-preview.de.md`](docs/hourly-preview.de.md). Sprechen im Browser benötigt HTTPS: [`docs/https-mic.de.md`](docs/https-mic.de.md).

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

## Add-on-Optionen

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

## Begleitintegration (HACS)

Nach Schritt 3 stehen folgende Entitäten zur Verfügung:

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

## Beispiel-Dashboard & go2rtc

- Lovelace-Beispiel (Standbild mit `camera_view: auto` + Start/Stop + Klingeln): [`dashboards/kuechen-panel-example.yaml`](dashboards/kuechen-panel-example.yaml)
- go2rtc-Stream zum Einfügen: [`docs/go2rtc-comelit-icona.yaml`](docs/go2rtc-comelit-icona.yaml)
- Paket / Blaupause für die stündliche Vorschau (kurzes LED-Aufleuchten): [`docs/hourly-preview.de.md`](docs/hourly-preview.de.md)
- HTTPS für das Browser-Mikrofon + Behebung von `http:`-Migrationsproblemen: [`docs/https-mic.de.md`](docs/https-mic.de.md)

```yaml
streams:
  comelit_icona:
    - rtsp://127.0.0.1:8557/intercom
```

### Paket für die stündliche Vorschau installieren

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

[`packages/hourly_klingel_preview.yaml`](packages/hourly_klingel_preview.yaml) nach `config/packages/` kopieren, sicherstellen, dass `/media/comelit_icona/` existiert, und Automationen neu laden. Alternativ die Blaupause aus [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml) importieren. Beim Ablauf Start→Standbild→Stop ist einmal pro Stunde ein **kurzes Aufleuchten der Außen-LEDs** zu erwarten.

## Bezugsquellen

- [Comelit 6741W auf Amazon.de suchen (Prime-Filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6741W&rh=p_85%3A20943776031)\*
- [Comelit 6701W auf Amazon.de suchen (Prime-Filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6701W&rh=p_85%3A20943776031)\*

\*Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Mit * markierte Links sind Werbe-/Affiliate-Links.

## Danksagung

Gepflegt von [atomi23](https://github.com/atomi23).

ICONA-Protokollclient, CTPP-/Videoanruf, VIP-Listener, RTP-Empfänger und lokaler RTSP-Server sind **angepasste Versionen aus** [`mnestrud/comelit-man`](https://github.com/mnestrud/comelit-man) (Apache-2.0; siehe `NOTICE` / `LICENSE`).

## Lizenz

Apache License 2.0
