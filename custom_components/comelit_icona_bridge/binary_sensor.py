"""Ringing / connectivity binary sensors for the ICONA Bridge add-on."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_API_URL, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)
SCAN = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors backed by add-on /status."""
    session = async_get_clientsession(hass)
    api = entry.data[CONF_API_URL].rstrip("/")

    async def _fetch() -> dict:
        try:
            async with session.get(f"{api}/status", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status >= 400:
                    return {"connected": False, "ringing": False}
                return await resp.json()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("status poll failed", exc_info=True)
            return {"connected": False, "ringing": False}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="comelit_icona_bridge_status",
        update_method=_fetch,
        update_interval=SCAN,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[f"{entry.entry_id}_coord"] = coordinator
    async_add_entities(
        [
            IconaFlagSensor(coordinator, entry, "ringing", "Klingelt", BinarySensorDeviceClass.SOUND),
            IconaFlagSensor(
                coordinator, entry, "connected", "ICONA Verbindung", BinarySensorDeviceClass.CONNECTIVITY
            ),
        ]
    )


class IconaFlagSensor(CoordinatorEntity, BinarySensorEntity):
    """Boolean flag from add-on /status."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        device_class: BinarySensorDeviceClass,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"comelit_icona_bridge_{key}"
        self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Comelit ICONA Bridge",
            "manufacturer": "Comelit",
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return bool(data.get(self._key))
