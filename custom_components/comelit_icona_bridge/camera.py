"""Camera entity backed by the ICONA Bridge add-on RTSP URL."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

import aiohttp
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.components.ffmpeg import async_get_image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_URL, CONF_RTSP_URL, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)

# Set while HA only inspects the stream source (e.g. WebRTC provider lookup on
# startup), so stream_source() must not wake up the panel.
_PROBING_PROVIDERS: ContextVar[bool] = ContextVar("icona_probing_providers", default=False)


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
        self._last_image: bytes | None = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Comelit ICONA Bridge",
            "manufacturer": "Comelit",
            "model": MODEL,
        }

    @property
    def _api(self) -> str:
        return self._entry.data[CONF_API_URL].rstrip("/")

    async def async_refresh_providers(self, *args: Any, **kwargs: Any) -> None:
        """Look up WebRTC providers without starting ICONA video."""
        token = _PROBING_PROVIDERS.set(True)
        try:
            await super().async_refresh_providers(*args, **kwargs)
        finally:
            _PROBING_PROVIDERS.reset(token)

    async def stream_source(self) -> str | None:
        """Start ICONA video via the add-on API, then return the RTSP URL."""
        if not _PROBING_PROVIDERS.get():
            await self._start_video()
        return self._entry.data[CONF_RTSP_URL]

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a frame while video runs, otherwise the last captured frame.

        Never starts video itself: dashboards poll stills, and starting ICONA
        video switches on the outdoor panel LEDs.
        """
        if await self._video_active():
            image = await async_get_image(
                self.hass,
                f"-rtsp_transport tcp -i {self._entry.data[CONF_RTSP_URL]}",
                width=width,
                height=height,
            )
            if image:
                self._last_image = image
        return self._last_image

    async def _start_video(self) -> None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{self._api}/start", timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    _LOGGER.error("ICONA bridge /start failed: %s %s", resp.status, body[:200])
        except Exception:  # noqa: BLE001
            _LOGGER.exception("ICONA bridge /start request failed")

    async def _video_active(self) -> bool:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{self._api}/status", timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("ICONA bridge /status request failed", exc_info=True)
            return False
        return bool(data.get("video_active"))
