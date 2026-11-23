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


def call_frame(prefix, timestamp, action):
    return struct.pack("<HI", prefix, timestamp) + struct.pack(">HH", action, 0) + b"SB100001\x00SB0000060\x00"


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

    async def assert_ring_status(self, api, *, ringing, pending, ring_ts=None):
        status = await (await api.get("/status")).json()
        self.assertEqual(
            (status["ringing"], status["pending_inbound"]),
            (ringing, pending),
            f"/status: ringing={status['ringing']}, pending_inbound={status['pending_inbound']}",
        )
        if ring_ts is not None:
            self.assertEqual(status["last_ring"]["ring_ts"], ring_ts)
        return status

    async def panel_frame(self, prefix, timestamp, action):
        with patch.object(self.panel, "send_binary", new_callable=AsyncMock):
            await self.service._vip._process_message(call_frame(prefix, timestamp, action))

    async def test_idle_clears_only_matching_ring(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            await self.panel_frame(0x18C0, 0x01010001, 1)
            await self.panel_frame(0x18C0, 0x01010002, 1)
            await self.panel_frame(0x1840, 0x02020001, 0)
            await self.assert_ring_status(api, ringing=True, pending=True, ring_ts=0x01010002)
            await self.panel_frame(0x1840, 0x02020002, 0)
            await self.assert_ring_status(api, ringing=False, pending=False, ring_ts=0x01010002)

    async def test_idle_clears_alerting_without_call_init(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            await self.panel_frame(0x1860, 0x01010001, 1)
            await self.assert_ring_status(api, ringing=True, pending=False)
            await self.panel_frame(0x1840, 0x02020001, 0)
            await self.assert_ring_status(api, ringing=False, pending=False)

    async def test_stop_clears_pending_ring_without_video(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            await self.panel_frame(0x18C0, 123, 1)
            await self.assert_ring_status(api, ringing=True, pending=True)
            self.assertEqual((await api.post("/stop")).status, 200)
            await self.assert_ring_status(api, ringing=False, pending=False, ring_ts=123)

    async def start_inbound_successfully(self):
        async def start(session, *args, **kwargs):
            session._active = True

        await self.panel_frame(0x18C0, 123, 1)
        with patch.object(VideoCallSession, "start_inbound", start):
            await self.service.start_inbound()
        return self.service.session

    async def check_inbound_timeout(self, *, newer_ring):
        async with TestClient(TestServer(build_app(self.service))) as api:
            session = await self.start_inbound_successfully()
            await self.assert_ring_status(api, ringing=True, pending=True, ring_ts=123)
            if newer_ring:
                session._forward_ring(call_frame(0x18C0, 124, 1))
            with patch("icona.video_call.VIDEO_SESSION_TIMEOUT", 0):
                await session._auto_timeout_loop()
            status = await self.assert_ring_status(
                api, ringing=newer_ring, pending=newer_ring, ring_ts=124 if newer_ring else 123,
            )
            self.assertFalse(status["video_active"])
            self.assertIsNone(self.service.session)

    async def test_timeout_clears_its_inbound_ring(self):
        await self.check_inbound_timeout(newer_ring=False)

    async def test_old_timeout_keeps_newer_ring(self):
        await self.check_inbound_timeout(newer_ring=True)

    async def test_old_stop_keeps_newer_ring(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            session = await self.start_inbound_successfully()
            session._forward_ring(call_frame(0x18C0, 124, 1))
            self.assertEqual((await api.post("/stop")).status, 200)
            await self.assert_ring_status(api, ringing=True, pending=True, ring_ts=124)

    async def test_idle_during_live_view_clears_only_its_ring(self):
        async with TestClient(TestServer(build_app(self.service))) as api:
            session = await self.start_successfully()

            async def process_frames(*frames):
                read_response = AsyncMock(side_effect=[*frames, asyncio.CancelledError])
                with (
                    patch.object(self.panel, "read_response", read_response, create=True),
                    patch.object(self.panel, "send_binary", new_callable=AsyncMock),
                ):
                    await session._ctpp_monitor_loop(
                        self.panel, self.panel.ctpp, "SB0000060", "SB100001", 0, 0, 0,
                    )

            await process_frames(call_frame(0x18C0, 0x01010002, 1), call_frame(0x1840, 0x02020001, 0))
            status = await self.assert_ring_status(api, ringing=True, pending=True, ring_ts=0x01010002)
            self.assertTrue(status["video_active"])

            await process_frames(call_frame(0x1840, 0x02020002, 0))
            self.assertTrue(session.active)
            self.assertEqual((await api.post("/stop")).status, 200)
            await self.assert_ring_status(api, ringing=False, pending=False, ring_ts=0x01010002)


if __name__ == "__main__":
    unittest.main()
