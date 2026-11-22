[Deutsch](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.md) | **English**

[Installation](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/installation.en.md) · [Options](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/options.en.md) · [Entities](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/entities.en.md) · [Dashboard](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/dashboard-go2rtc.en.md) · [Hourly preview](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md) · [HTTPS microphone](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

# Sample dashboard & go2rtc

- Lovelace example (still `camera_view: auto` + Start/Stop + ringing): [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml)
- One-paste go2rtc stream: [`docs/go2rtc-comelit-icona.yaml`](../docs/go2rtc-comelit-icona.yaml)
- Hourly preview package / blueprint (short LED blink): [`docs/hourly-preview.en.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/hourly-preview.en.md)
- HTTPS for browser mic + `http:` migration repair: [`docs/https-mic.en.md`](https://github.com/atomi23/ha-comelit-icona-bridge/blob/main/docs/https-mic.en.md)

```yaml
streams:
  comelit_icona:
    - rtsp://127.0.0.1:8557/intercom
```

### Install hourly preview package

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

Copy [`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) into `config/packages/`, ensure `/media/comelit_icona/` exists, reload automations. Or import the blueprint from [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](../blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml). Expect a **brief outdoor LED blink** once per hour during start→snapshot→stop.
