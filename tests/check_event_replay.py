"""Check doorbell replay suppression in a Home Assistant Core runtime."""

import asyncio
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from aiohttp import web
from homeassistant import loader
from homeassistant.bootstrap import async_from_config_dict
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant

from custom_components.comelit_icona_bridge.const import CONF_API_URL
from custom_components.comelit_icona_bridge.event import IconaDoorbellEvent, async_setup_entry


async def check(config_dir: Path) -> None:
    hass = HomeAssistant(str(config_dir))
    loader.async_setup(hass)
    events = [{"type": "ring", "ts": time.time() - 3600}]
    status = 200

    async def feed(_: web.Request) -> web.Response:
        return web.json_response({"events": events}, status=status)

    app = web.Application()
    app.router.add_get("/events", feed)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    entry = SimpleNamespace(
        entry_id="test", data={CONF_API_URL: f"http://127.0.0.1:{port}"},
        async_on_unload=lambda _cancel: None,
    )
    try:
        if await async_from_config_dict({"homeassistant": {}}, hass) is None:
            raise RuntimeError("Home Assistant Core setup failed")
        print(f"Home Assistant Core {__version__}", flush=True)
        for label, initial_status, initial_events in (
            ("buffered ring", 200, events.copy()),
            ("empty feed", 200, []),
            ("failed initial poll", 500, events.copy()),
        ):
            status = initial_status
            events = initial_events
            entities = []
            with (
                patch("custom_components.comelit_icona_bridge.event.async_track_time_interval") as track,
                patch.object(IconaDoorbellEvent, "async_write_ha_state"),
            ):
                await async_setup_entry(hass, entry, entities.extend)
                (entity,) = entities
                assert isinstance(entity, IconaDoorbellEvent)
                assert entity.state is None, f"{label}: replayed an old ring on setup"
                poll = track.call_args.args[1]
                if status == 500:
                    status = 200
                    await poll()
                    assert entity.state is None, "First successful poll replayed history"
                new_ring = {"type": "ring", "ts": time.time()}
                events.append(new_ring)
                with patch.object(entity, "_trigger_event", wraps=entity._trigger_event) as trigger:
                    await poll()
                    await poll()
                    trigger.assert_called_once_with("ring", new_ring)
                assert entity.state_attributes["event_type"] == "ring"
                print(f"{label}: no replay; new ring fired exactly once [PASS]", flush=True)
    finally:
        await hass.async_stop(force=True)
        await runner.cleanup()


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        asyncio.run(check(Path(directory)))
