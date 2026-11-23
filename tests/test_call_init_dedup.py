"""Regression repro: python -m unittest discover -s tests -p test_call_init_dedup.py -v."""

import asyncio
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comelit_icona_bridge/rootfs/opt/icona_bridge"))

from main import IconaBridgeService, build_app
from icona.models import DeviceConfig
from icona.video_call import VideoCallSession


def call_init(caller="SB100001", timestamp=123):
    return struct.pack("<HI", 0x18C0, timestamp) + b"\x00\x01\x00\x00" + caller.encode() + b"\x00SB0000060\x00"


class CallInitDedupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = IconaBridgeService({"host": "fake-panel", "auto_start_on_ring": False})
        ctpp = SimpleNamespace(response_queue=asyncio.Queue())
        self.service.client = SimpleNamespace(get_channel=lambda name: ctpp if name == "CTPP" else None)
        self.service.device_config = DeviceConfig(apt_address="SB000006", caller_address="SB100001")
        await self.service._start_vip_listener()
        self.addAsyncCleanup(self.service._vip.stop)
        self.api = await self.enterAsyncContext(TestClient(TestServer(build_app(self.service))))

    async def ring_events(self):
        response = await self.api.get("/events")
        self.assertEqual(response.status, 200)
        return [(event["entrance"], event["ring_ts"]) for event in (await response.json())["events"]]

    async def test_three_identical_call_init_frames_publish_one_ring(self):
        frame = call_init()
        for _ in range(3):
            await self.service._vip._process_message(frame)

        self.assertEqual(await self.ring_events(), [("SB100001", 123)])

    async def test_distinct_rings_survive_and_mid_call_retransmit_does_not(self):
        for frame in (call_init(), call_init(timestamp=124), call_init("SB100002", timestamp=124)):
            await self.service._vip._process_message(frame)

        video = VideoCallSession(self.service.client, self.service.device_config, on_ring=self.service._on_mid_call_ring)
        video._forward_ring(call_init())
        video._forward_ring(call_init("SB100002", timestamp=125))

        self.assertEqual(
            await self.ring_events(), [("SB100001", 123), ("SB100001", 124), ("SB100002", 124), ("SB100002", 125)]
        )
