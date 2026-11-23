"""Check bridge discovery and entry validation in Home Assistant Core."""

import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aiohttp import ClientSession, web
from homeassistant.config_entries import SOURCE_USER, ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.comelit_icona_bridge import config_flow
from custom_components.comelit_icona_bridge.const import (
    CONF_API_URL,
    CONF_RTSP_URL,
    DOMAIN,
)


class BridgeStatusConfigFlowTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.hass = HomeAssistant(directory.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.addAsyncCleanup(self.hass.async_stop, force=True)
        session = await self.enterAsyncContext(ClientSession())
        self.enterContext(
            patch.object(config_flow, "async_get_clientsession", return_value=session)
        )

        self.bridge_status = {
            "connected": False,
            "video_active": False,
            "rtsp_url": "rtsp://127.0.0.1:18557/intercom",
            "rtsp_port": 18557,
        }
        app = web.Application()
        app.router.add_get("/{kind}/status", self.status)
        app.router.add_get("/status", self.status)
        runner = web.AppRunner(app)
        await runner.setup()
        self.addAsyncCleanup(runner.cleanup)
        await web.TCPSite(runner, "127.0.0.1", 0).start()
        self.port = runner.addresses[0][1]

    async def status(self, request: web.Request) -> web.Response:
        kind = request.match_info.get("kind", request.host.partition(":")[0])
        if kind == "text":
            return web.Response(text="OK")
        if kind in ("json", "127.0.0.1"):
            return web.json_response({"status": "ok"})
        if kind == "unavailable":
            return web.json_response(self.bridge_status, status=503)
        return web.json_response(self.bridge_status)

    def flow(self) -> config_flow.ConfigFlow:
        flow = config_flow.ConfigFlow()
        flow.hass = self.hass
        flow.handler = DOMAIN
        flow.context = {"source": SOURCE_USER}
        flow.flow_id = "test"
        return flow

    async def test_discovery_skips_unrelated_json_and_uses_bridge_rtsp_port(
        self,
    ) -> None:
        with (
            patch.object(config_flow, "DEFAULT_API_PORT", self.port),
            patch.object(
                config_flow, "_candidate_hosts", return_value=["127.0.0.1", "localhost"]
            ),
        ):
            result = await self.flow().async_step_user()

        self.assertEqual(result["step_id"], "confirm")
        self.assertEqual(
            result["description_placeholders"],
            {
                "api_url": f"http://localhost:{self.port}",
                "rtsp_url": "rtsp://127.0.0.1:18557/intercom",
            },
        )

    async def test_manual_setup_rejects_unrelated_or_failed_responses(self) -> None:
        for kind in ("text", "json", "unavailable"):
            with self.subTest(kind=kind):
                result = await self.flow().async_step_manual(
                    {
                        CONF_API_URL: f"http://127.0.0.1:{self.port}/{kind}",
                        CONF_RTSP_URL: self.bridge_status["rtsp_url"],
                    }
                )
                self.assertEqual(result["type"], FlowResultType.FORM)
                self.assertEqual(result["errors"], {"base": "cannot_connect"})

    async def test_manual_setup_accepts_disconnected_bridge_without_rtsp_port(
        self,
    ) -> None:
        self.bridge_status.pop("rtsp_port")
        result = await self.flow().async_step_manual(
            {
                CONF_API_URL: f"http://127.0.0.1:{self.port}/bridge/",
                CONF_RTSP_URL: self.bridge_status["rtsp_url"],
            }
        )
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
