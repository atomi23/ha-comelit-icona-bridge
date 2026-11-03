"""Config flow for the companion ICONA bridge camera."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_URL,
    CONF_RTSP_URL,
    DEFAULT_API_PORT,
    DEFAULT_API_URL,
    DEFAULT_RTSP_PATH,
    DEFAULT_RTSP_PORT,
    DEFAULT_RTSP_URL,
    DISCOVERY_HOSTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _host_from_ha_url(url: str | None) -> str | None:
    """Extract hostname from a HA base URL."""
    if not url:
        return None
    try:
        host = urlparse(url).hostname
    except ValueError:
        return None
    return host or None


def _candidate_hosts(hass: HomeAssistant) -> list[str]:
    """Build ordered unique host candidates for :8099/status discovery."""
    hosts: list[str] = []

    for attr in ("internal_url", "external_url"):
        host = _host_from_ha_url(getattr(hass.config, attr, None))
        if host:
            hosts.append(host)

    try:
        from homeassistant.helpers.network import get_url

        host = _host_from_ha_url(
            get_url(hass, prefer_external=False, allow_cloud=False)
        )
        if host:
            hosts.append(host)
    except Exception:  # noqa: BLE001 — helpers vary by HA version
        _LOGGER.debug("get_url host detection skipped", exc_info=True)

    hosts.extend(DISCOVERY_HOSTS)

    # Preserve order, drop empties / duplicates (case-insensitive).
    seen: set[str] = set()
    ordered: list[str] = []
    for host in hosts:
        key = host.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(host.strip())
    return ordered


def _rtsp_for_api(api_url: str) -> str:
    """Derive a matching RTSP URL; prefer loopback when API is on this HA host."""
    host = urlparse(api_url).hostname or "127.0.0.1"
    if host.lower() in {"127.0.0.1", "localhost", "homeassistant.local", "supervisor", "homeassistant", "hassio"}:
        host = "127.0.0.1"
    return f"rtsp://{host}:{DEFAULT_RTSP_PORT}/{DEFAULT_RTSP_PATH}"


async def _probe_status(hass: HomeAssistant, api_url: str) -> bool:
    """Return True when GET {api_url}/status succeeds."""
    session = async_get_clientsession(hass)
    url = api_url.rstrip("/") + "/status"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as resp:
            if resp.status >= 400:
                return False
            await resp.json(content_type=None)
            return True
    except Exception:  # noqa: BLE001
        return False


async def _discover_api(hass: HomeAssistant) -> str | None:
    """Probe common hosts for a live add-on control API."""
    for host in _candidate_hosts(hass):
        api_url = f"http://{host}:{DEFAULT_API_PORT}"
        if await _probe_status(hass, api_url):
            _LOGGER.info("Discovered ICONA Bridge API at %s", api_url)
            return api_url
    return None


async def _validate(hass: HomeAssistant, api_url: str) -> None:
    """Reachability check against the add-on control API (raises on failure)."""
    session = async_get_clientsession(hass)
    url = api_url.rstrip("/") + "/status"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
        resp.raise_for_status()


def _schema(rtsp_default: str, api_default: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_API_URL, default=api_default): str,
            vol.Required(CONF_RTSP_URL, default=rtsp_default): str,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow with optional :8099 discovery."""

    VERSION = 1

    def __init__(self) -> None:
        self._suggested_api = DEFAULT_API_URL
        self._suggested_rtsp = DEFAULT_RTSP_URL
        self._discovered = False

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Discover a live add-on when possible, then confirm / edit URLs."""
        if user_input is not None:
            return await self._async_create(user_input)

        discovered = await _discover_api(self.hass)
        if discovered:
            self._suggested_api = discovered
            self._suggested_rtsp = _rtsp_for_api(discovered)
            self._discovered = True
            return await self.async_step_confirm()

        return await self.async_step_manual()

    async def async_step_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Confirm auto-detected URLs (still editable)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self._async_create(user_input)

        return self.async_show_form(
            step_id="confirm",
            data_schema=_schema(self._suggested_rtsp, self._suggested_api),
            errors=errors,
            description_placeholders={
                "api_url": self._suggested_api,
                "rtsp_url": self._suggested_rtsp,
            },
        )

    async def async_step_manual(self, user_input: dict | None = None) -> FlowResult:
        """Manual entry with HA-friendly defaults when discovery finds nothing."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self._async_create(user_input)

        # Prefer HA-configured host in the default API URL even without a live probe.
        hosts = _candidate_hosts(self.hass)
        if hosts:
            preferred = next(
                (h for h in hosts if h.lower() not in {"supervisor", "homeassistant", "hassio"}),
                hosts[0],
            )
            self._suggested_api = f"http://{preferred}:{DEFAULT_API_PORT}"
            self._suggested_rtsp = _rtsp_for_api(self._suggested_api)

        return self.async_show_form(
            step_id="manual",
            data_schema=_schema(self._suggested_rtsp, self._suggested_api),
            errors=errors,
        )

    async def _async_create(self, user_input: dict) -> FlowResult:
        """Validate and create the config entry."""
        errors: dict[str, str] = {}
        await self.async_set_unique_id("comelit_icona_bridge")
        self._abort_if_unique_id_configured()
        try:
            await _validate(self.hass, user_input[CONF_API_URL])
        except Exception:  # noqa: BLE001 — surface as cannot_connect
            errors["base"] = "cannot_connect"
            step_id = "confirm" if self._discovered else "manual"
            return self.async_show_form(
                step_id=step_id,
                data_schema=_schema(
                    user_input.get(CONF_RTSP_URL, self._suggested_rtsp),
                    user_input.get(CONF_API_URL, self._suggested_api),
                ),
                errors=errors,
                description_placeholders={
                    "api_url": user_input.get(CONF_API_URL, self._suggested_api),
                    "rtsp_url": user_input.get(CONF_RTSP_URL, self._suggested_rtsp),
                },
            )

        return self.async_create_entry(
            title="Comelit ICONA Bridge Camera",
            data=user_input,
        )
