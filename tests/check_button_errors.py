"""Press the companion buttons in a Home Assistant Core runtime against a fake bridge."""

import asyncio
import socket
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from aiohttp import web
from homeassistant import loader
from homeassistant.bootstrap import async_from_config_dict
from homeassistant.components.button import DATA_COMPONENT
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import translation
from homeassistant.setup import async_setup_component

from custom_components.comelit_icona_bridge.button import IconaApiButton
from custom_components.comelit_icona_bridge.const import CONF_API_URL, DOMAIN


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def start_fake_bridge() -> tuple[web.AppRunner, str]:
    async def start(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "active": True})

    async def door(_: web.Request) -> web.Response:
        return web.json_response(
            {"ok": False, "error": "No doors in device config", "active": False},
            status=500,
        )

    app = web.Application()
    app.router.add_post("/start", start)
    app.router.add_post("/door", door)
    runner = web.AppRunner(app)
    await runner.setup()
    port = free_port()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    return runner, f"http://127.0.0.1:{port}"


async def check(config_dir: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    (config_dir / "custom_components").symlink_to(
        repo / "custom_components", target_is_directory=True
    )

    hass = HomeAssistant(str(config_dir))
    loader.async_setup(hass)
    runner, bridge_url = await start_fake_bridge()
    failures = []
    try:
        if await async_from_config_dict({"homeassistant": {}}, hass) is None:
            raise RuntimeError("Home Assistant Core setup failed")
        assert await async_setup_component(hass, "button", {})
        hass.config.components.add(DOMAIN)  # a config entry would mark it loaded
        for language in ("en", "de"):
            await translation.async_get_translations(hass, language, "exceptions", {DOMAIN})
        german = translation.async_get_cached_translations(hass, "de", "exceptions", DOMAIN)

        cases = (
            ("start, Bridge OK", bridge_url, "start", False),
            ("door, Bridge HTTP 500", bridge_url, "door", True),
            ("door, Bridge nicht erreichbar", f"http://127.0.0.1:{free_port()}", "door", True),
        )
        buttons = [
            IconaApiButton(
                SimpleNamespace(entry_id=label, data={CONF_API_URL: url}), f"case{i}", label, path
            )
            for i, (label, url, path, _) in enumerate(cases)
        ]
        await hass.data[DATA_COMPONENT].async_add_entities(buttons)

        print(f"Home Assistant Core {__version__}", flush=True)
        for (label, _, _, should_raise), button in zip(cases, buttons):
            try:
                await hass.services.async_call(
                    "button", "press", target={"entity_id": button.entity_id}, blocking=True
                )
                outcome, raised = "Dienstaufruf erfolgreich", False
            except HomeAssistantError as err:
                key = f"component.{DOMAIN}.exceptions.{err.translation_key}.message"
                localized = german[key].format(**err.translation_placeholders)
                outcome, raised = f"HomeAssistantError: {err}\n  de: {localized}", True
            passed = raised == should_raise
            print(f"{label}: {outcome} [{'PASS' if passed else 'FAIL'}]", flush=True)
            if not passed:
                failures.append(label)
    finally:
        await hass.async_stop(force=True)
        await runner.cleanup()

    if failures:
        raise AssertionError(f"Unexpected outcome for: {failures}")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        asyncio.run(check(Path(directory)))
