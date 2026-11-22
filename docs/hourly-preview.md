# Hourly Klingel preview (PN-32)

Goal: keep a fresh **still** of the outdoor camera on a kitchen/panel dashboard **without** leaving ICONA live video (and outdoor LEDs) on.

## Why not `camera_view: live`?

`picture-entity` with `camera_view: live` opens the RTSP path and typically calls `/start`, which can turn on the panel’s outdoor LEDs. Each ICONA video session ends after 120 s, then the ring listener resumes if enabled and connected. Use **`camera_view: auto`** for stills. Keep the Start / Stop tiles for on-demand video control.

HA startup does not start video. The companion grabs a still frame while video is active; otherwise it returns the last cached frame. This cache is memory-only, empty after an HA restart, and not restored from the saved JPEG.

## Package or blueprint

| Path | Role |
|------|------|
| [`packages/hourly_klingel_preview.yaml`](../packages/hourly_klingel_preview.yaml) | Drop-in HA **package** (automation) |
| [`blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml`](../blueprints/automation/comelit_icona_bridge/hourly_klingel_preview.yaml) | Same flow as a **blueprint** (UI inputs) |
| [`dashboards/kuechen-panel-example.yaml`](../dashboards/kuechen-panel-example.yaml) | Lovelace example: `camera_view: auto` + Start/Stop |

### Install via `packages:`

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

Copy `packages/hourly_klingel_preview.yaml` into `config/packages/`, create `/media/comelit_icona/`, restart (or reload automations).

### Install via blueprint

Copy the blueprint file into `config/blueprints/automation/comelit_icona_bridge/`, create `/media/comelit_icona/` (as for the package), then **Settings → Automations & scenes → Create automation** and pick **ICONA hourly Klingel preview**.

## LED behaviour

Each hourly run: **Start** → ~4s settle → **snapshot** → **Stop**. Outdoor IR/white LEDs may **blink briefly** once per hour. That is expected. If the blink is too long, lower settle seconds (blueprint input / edit the package delay); if snapshots are black, raise slightly (e.g. 5–6s).

The package and blueprint use `continue_on_error: true` on `camera.snapshot` so Stop still runs after a failed snapshot. Companion buttons show an HA error if the bridge call fails.

## Optional go2rtc frame

If you already run AlexxIT go2rtc with `comelit_icona` (see [`go2rtc-comelit-icona.yaml`](go2rtc-comelit-icona.yaml)), you can grab a JPEG via go2rtc’s frame API instead of `camera.snapshot` after `/start`. The package comments show where to swap that in. This updates only the file, not the companion camera’s cached still; use a media/file picture card to display it (see the commented example in `dashboards/kuechen-panel-example.yaml`). You still must **Stop** promptly so LEDs turn off.
