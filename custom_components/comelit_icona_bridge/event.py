"""Doorbell event entity fed from the ICONA Bridge add-on /events feed."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_API_URL, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)
POLL = timedelta(seconds=2)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the doorbell event entity."""
    entity = IconaDoorbellEvent(entry)
    async_add_entities([entity])

    session = async_get_clientsession(hass)
    api = entry.data[CONF_API_URL].rstrip("/")
    last_seen: dict[str, float] = {"ts": 0.0}

    async def _poll(_now=None) -> None:
        try:
            async with session.get(f"{api}/events", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status >= 400:
                    return
                payload = await resp.json()
        except Exception:  # noqa: BLE001
            return
        for evt in payload.get("events") or []:
            ts = float(evt.get("ts") or 0)
            if ts <= last_seen["ts"]:
                continue
            last_seen["ts"] = ts
            etype = str(evt.get("type") or "unknown")
            if etype in ("ring", "missed_call", "door_opened", "answered", "video_started", "video_stopped"):
                entity._trigger(etype, evt)

    entry.async_on_unload(async_track_time_interval(hass, _poll, POLL))
    await _poll()


class IconaDoorbellEvent(EventEntity):
    """Fires when the add-on reports a doorbell / call event."""

    _attr_has_entity_name = True
    _attr_name = "Klingel"
    _attr_event_types = [
        "ring",
        "missed_call",
        "door_opened",
        "answered",
        "video_started",
        "video_stopped",
    ]
    _attr_unique_id = "comelit_icona_bridge_doorbell"

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Comelit ICONA Bridge",
            "manufacturer": "Comelit",
            "model": MODEL,
        }

    def _trigger(self, event_type: str, data: dict) -> None:
        self._trigger_event(event_type, data)
        self.async_write_ha_state()
