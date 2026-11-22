"""Regression repro: python -m unittest discover -s tests -p test_vip_video_recovery.py -v."""

import asyncio
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comelit_icona_bridge/rootfs/opt/icona_bridge"))

from main import IconaBridgeService, build_app
from icona.exceptions import VideoCallError
from icona.models import DeviceConfig
from icona.video_call import VideoCallSession


class FakePanelTransport:
    """Shared CTPP queue with a panel that rejects video signaling."""

    connected = True

    def __init__(self):
        self.ctpp = SimpleNamespace(response_queue=asyncio.Queue(), server_channel_id=1)

    def get_channel(self, name):
        return self.ctpp if name in ("CTPP", "CSPB") else None

    def register_placeholder_channel(self, name):
        return SimpleNamespace()

    def remove_channel(self, name):
        pass

    async def send_binary(self, channel, payload):
        raise ConnectionError("Simulated panel rejected video signaling")

    def ring(self):
        self.ctpp.response_queue.put_nowait(
            struct.pack("<HI", 0x18C0, 123) + b"\x00\x01\x00\x00SB100001\x00SB0000060\x00"
        )


class VipVideoRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = IconaBridgeService({"host": "fake-panel", "auto_start_on_ring": False})
        self.panel = FakePanelTransport()
        self.service.client = self.panel
        self.service.device_config = DeviceConfig(apt_address="SB000006", caller_address="SB100001")
        self.service.ensure_rtsp = AsyncMock()
        self.service._ctpp_init_ts = 1
        await self.service._start_vip_listener()

    async def asyncTearDown(self):
        if self.service.session:
            await self.service.session.stop()
        if self.service._vip:
            await self.service._vip.stop()

    async def assert_next_ring_received(self):
        self.panel.ring()
        for _ in range(30):
            if self.service._pending_inbound:
                break
            await asyncio.sleep(0.01)
        self.assertIsNotNone(self.service._pending_inbound, "VIP did not process the next panel ring")

    async def test_outgoing_http_500_restores_vip(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            response = await api.post("/start")
            self.assertEqual(response.status, 500)
            status = await (await api.get("/status")).json()
            self.assertTrue(status["vip_listener"])
            self.assertFalse(status["video_active"])
            await self.assert_next_ring_received()

    async def test_incoming_video_error_restores_vip(self):
        with self.assertRaises(VideoCallError):
            await self.service.start_inbound("SB100001", 123)
        await self.assert_next_ring_received()

    async def start_successfully(self, timeout=False):
        async def start(session):
            session._active = True
            session._owns_ctpp = False
            if timeout:
                session._timeout_task = asyncio.create_task(session._auto_timeout_loop())

        with patch.object(VideoCallSession, "start", start):
            await self.service.start_video()
        return self.service.session

    async def test_auto_timeout_restores_vip(self):
        with patch("icona.video_call.VIDEO_SESSION_TIMEOUT", 0.01):
            session = await self.start_successfully(timeout=True)
            await asyncio.wait_for(asyncio.shield(session._timeout_task), 1)
        await self.assert_next_ring_received()
        self.assertIsNone(self.service.session)

    async def test_stale_call_end_does_not_clobber_new_session(self):
        await self.check_stale_callback("_on_call_end")

    async def test_stale_timeout_does_not_clobber_new_session(self):
        await self.check_stale_callback("_on_timeout")

    async def check_stale_callback(self, name):
        old = await self.start_successfully()
        callback = getattr(old, name)
        self.assertIsNotNone(callback, "Session completion callback is not wired")
        old._active = False
        async with self.service._session_lock:
            callback()
            self.assertIs(self.service.session, old, "Callback bypassed session lock")
        new = await self.start_successfully()
        await asyncio.sleep(0.02)
        self.assertIs(self.service.session, new, "Old callback cleared the newer session")
        self.assertTrue(new.active)
        self.assertIsNone(self.service._vip._task, "VIP stole CTPP from the newer session")

    async def test_explicit_stop_restores_vip(self):
        await self.start_successfully()
        await self.service.stop_video()
        await self.assert_next_ring_received()


if __name__ == "__main__":
    unittest.main()
