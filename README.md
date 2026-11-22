**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/README.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# ha-comelit-icona-bridge

Home-Assistant-**Add-on**, das eine lokale **ICONA-/VIPER**-Sitzung zu einer Comelit-WLAN-Videosprechanlage (**6741W** / 6701W-Familie, TCP **64100**) öffnet und die Außenkamera als **RTSP auf dem HA-Host** (`rtsp://<ha-ip>:8557/intercom`) für Lovelace / go2rtc / Generic Camera bereitstellt.

Begleitende HACS-Integration: Kamera + Start-/Stop-/Annehmen-/Tür-Tasten + Klingelsensor.

Keine Umgehung der Cloud-Authentifizierung. Kein Frida. Kein Mitschneiden von LAN-Paketen nötig — das Add-on spricht selbst ICONA.

## Schnellstart (3 Schritte)

1. **Add-on-Repository hinzufügen** — HA → **Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories** → hinzufügen:\
   `https://github.com/atomi23/ha-comelit-icona-bridge`\
   **Comelit ICONA Bridge** installieren (lokaler Docker-Build).

2. **Host + Token festlegen** — Optionen: IP-Adresse der Sprechanlage (`host`) und das ICONA-`token` aus 32 Hex-Zeichen. **`password` leer lassen** (optional; nur bei Modellen mit einer Web-Backup-Oberfläche sinnvoll — nicht beim üblichen 6741W-Zugang als Installer/Hausverwalter). Add-on starten. `http://<ha-ip>:8099/status` prüfen.

3. **HACS-Begleitintegration installieren** — HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → dieselbe GitHub-URL, Kategorie **Integration** → **Comelit ICONA Bridge Camera** herunterladen → HA neu starten → Integration hinzufügen. Die Erkennung prüft die API nur auf Port `8099`. Die vorgeschlagene RTSP-URL verwendet den erkannten Host (erkannte lokale Aliasnamen verwenden `127.0.0.1`) und den gültigen, von `/status` gemeldeten `rtsp_port` (Rückfallwert `8557`). Bei einem eigenen `api_port` beide URLs manuell eingeben.

## Seitenübersicht

- [Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md)
- [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md)
- [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md)
- [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md)
- [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md)
- [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

## Bezugsquellen

- [Comelit 6741W auf Amazon.de suchen (Prime-Filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6741W&rh=p_85%3A20943776031)\*
- [Comelit 6701W auf Amazon.de suchen (Prime-Filter)](https://www.amazon.de/s?tag=atomi23-21&k=Comelit+6701W&rh=p_85%3A20943776031)\*

\*Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Mit * markierte Links sind Werbe-/Affiliate-Links.
