"""Exercise the hourly preview automations in a Home Assistant Core runtime."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from homeassistant import loader
from homeassistant.bootstrap import async_from_config_dict
from homeassistant.config import async_hass_config_yaml
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError


async def check(config_dir: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    for folder in ("packages", "blueprints"):
        (config_dir / folder).symlink_to(repo / folder, target_is_directory=True)
    (config_dir / "configuration.yaml").write_text(
        """homeassistant:
  packages: !include_dir_named packages
automation:
  - id: preview_from_blueprint
    alias: Preview from blueprint
    use_blueprint:
      path: comelit_icona_bridge/hourly_klingel_preview.yaml
      input: {}
""",
        encoding="utf-8",
    )

    hass = HomeAssistant(str(config_dir))
    loader.async_setup(hass)
    calls = []
    fail_snapshot = False

    async def press(call: ServiceCall) -> None:
        (button,) = call.data["entity_id"]
        calls.append(
            {
                "button.comelit_icona_bridge_start_klingelvideo": "START",
                "button.comelit_icona_bridge_stop_klingelvideo": "STOP",
            }[button]
        )

    async def snapshot(_call: ServiceCall) -> None:
        calls.append("SNAPSHOT(fail)" if fail_snapshot else "SNAPSHOT(ok)")
        if fail_snapshot:
            raise HomeAssistantError("Simulated snapshot failure")

    failures = []
    try:
        config = await async_hass_config_yaml(hass)
        if await async_from_config_dict(config, hass) is None:
            raise RuntimeError("Home Assistant Core setup failed")
        hass.services.async_register("button", "press", press)
        hass.services.async_register("camera", "snapshot", snapshot)

        print(f"Home Assistant Core {__version__}", flush=True)
        for source, entity_id in (
            ("package", "automation.icona_hourly_klingel_preview_short_led_window"),
            ("blueprint", "automation.preview_from_blueprint"),
        ):
            for fail_snapshot in (False, True):
                calls.clear()
                await hass.services.async_call(
                    "automation",
                    "trigger",
                    target={"entity_id": entity_id},
                    blocking=True,
                )
                expected = [
                    "START",
                    "SNAPSHOT(fail)" if fail_snapshot else "SNAPSHOT(ok)",
                    "STOP",
                ]
                passed = calls == expected
                result = "PASS" if passed else "FAIL"
                print(f"{source}: {' → '.join(calls)} [{result}]", flush=True)
                if not passed:
                    failures.append((source, expected, calls.copy()))
    finally:
        await hass.async_stop(force=True)

    if failures:
        raise AssertionError(f"Expected and observed calls: {failures}")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        asyncio.run(check(Path(directory)))
