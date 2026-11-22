"""Start/Stop/Answer/Door buttons for the ICONA Bridge add-on."""

from __future__ import annotations

import json
import logging

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_URL, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up control buttons."""
    async_add_entities(
        [
            IconaApiButton(entry, "start", "Start Klingelvideo", "start"),
            IconaApiButton(entry, "stop", "Stop Klingelvideo", "stop"),
            IconaApiButton(entry, "answer", "Klingel annehmen / Sprechen", "answer"),
            IconaApiButton(entry, "door", "Tür öffnen", "door"),
        ]
    )


class IconaApiButton(ButtonEntity):
    """Call the add-on HTTP control API."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, key: str, name: str, path: str) -> None:
        self._entry = entry
        self._path = path
        self._attr_name = name
        self._attr_unique_id = f"comelit_icona_bridge_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Comelit ICONA Bridge",
            "manufacturer": "Comelit",
            "model": MODEL,
        }

    async def async_press(self) -> None:
        """POST control endpoint on the add-on."""
        api = self._entry.data[CONF_API_URL].rstrip("/")
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(f"{api}/{self._path}", timeout=aiohttp.ClientTimeout(total=45)) as resp:
                body = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="request_failed",
                translation_placeholders={"action": self._path, "error": str(err) or type(err).__name__},
            ) from err
        if resp.status >= 400:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="request_rejected",
                translation_placeholders={
                    "action": self._path,
                    "status": str(resp.status),
                    "error": _error_detail(body),
                },
            )
        _LOGGER.info("ICONA bridge /%s ok", self._path)


def _error_detail(body: str) -> str:
    """Return the bridge's error message, falling back to the raw response body."""
    try:
        return str(json.loads(body)["error"])
    except (ValueError, KeyError, TypeError):
        return body[:200]
