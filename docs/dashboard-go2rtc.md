**Deutsch** | [English](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md)

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.md) · [Optionen](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.md) · [Entitäten](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) · [Stündliche Vorschau](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md) · [HTTPS-Mikrofon](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

# Beispiel-Dashboard & go2rtc

- Lovelace-Beispiel (Standbild mit `camera_view: auto` + Start/Stop + Klingeln): [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml)
- go2rtc-Stream zum Einfügen: [`docs/go2rtc-comelit-icona.yaml`](../docs/go2rtc-comelit-icona.yaml)
- Paket / Blaupause für die stündliche Vorschau (kurzes LED-Aufleuchten): [`docs/hourly-preview.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.md)
- HTTPS für das Browser-Mikrofon + Behebung von `http:`-Migrationsproblemen: [`docs/https-mic.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.md)

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

[`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) nach `config/packages/` kopieren, sicherstellen, dass `/media/comelit_icona/` existiert, und Automationen neu laden. Alternativ die Blaupause aus [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](../blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml) importieren. Beim Ablauf Start→Standbild→Stop ist einmal pro Stunde ein **kurzes Aufleuchten der Außen-LEDs** zu erwarten.
