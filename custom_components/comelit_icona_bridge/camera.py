"""Camera entity backed by the ICONA Bridge add-on RTSP URL."""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_URL, CONF_RTSP_URL, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera entity."""
    async_add_entities([IconaBridgeCamera(entry)])


class IconaBridgeCamera(Camera):
    """Doorbell camera via local RTSP from the ICONA Bridge add-on."""

    _attr_has_entity_name = True
    _attr_name = "Klingelkamera"
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_unique_id = "comelit_icona_bridge_klingelkamera"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__()
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Comelit ICONA Bridge",
            "manufacturer": "Comelit",
            "model": MODEL,
        }

    async def stream_source(self) -> str | None:
        """Start ICONA video via the add-on API, then return the RTSP URL."""
        api = self._entry.data[CONF_API_URL].rstrip("/")
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(f"{api}/start", timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    _LOGGER.error("ICONA bridge /start failed: %s %s", resp.status, body[:200])
        except Exception:  # noqa: BLE001
            _LOGGER.exception("ICONA bridge /start request failed")
        return self._entry.data[CONF_RTSP_URL]
