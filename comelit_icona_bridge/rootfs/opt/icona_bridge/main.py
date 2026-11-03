#!/usr/bin/env python3
"""Standalone Comelit ICONA → local RTSP bridge for Home Assistant add-on.

Opens an ICONA session to the outdoor panel (TCP :64100) and republishes the
doorbell camera as a local RTSP stream (default :8557/intercom) plus a small HTTP
control API for start/stop/status, VIP ring events, answer/talk, and door open.

Verified against Comelit 6741W (VIPER :64100). Protocol core adapted from
mnestrud/comelit-man (Apache-2.0).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import signal
import time
from collections import deque
from pathlib import Path
from typing import Any

from aiohttp import web

from icona.auth import authenticate
from icona.channels import ChannelType
from icona.client import IconaBridgeClient
from icona.config_reader import get_device_config
from icona.ctpp import ctpp_init_sequence
from icona.door import open_door
from icona.exceptions import ComelitError, TokenExtractionError
from icona.models import PushEvent
from icona.rtsp_server import LocalRtspServer
from icona.token import extract_token
from icona.video_call import VideoCallSession
from icona.vip_listener import VipEventListener

LOG = logging.getLogger("icona_bridge")

OPTIONS_PATHS = (
    Path("/data/options.json"),
    Path(os.environ.get("ICONA_OPTIONS", "")),
    Path(__file__).resolve().parent / "options.json",
)


def load_options() -> dict[str, Any]:
    """Load add-on options (HA Supervisor writes /data/options.json)."""
    for path in OPTIONS_PATHS:
        if path and path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            LOG.info("Loaded options from %s", path)
            return data
    return {
        "host": os.environ.get("ICONA_HOST", "192.168.1.111"),
        "port": int(os.environ.get("ICONA_PORT", "64100")),
        "http_port": int(os.environ.get("ICONA_HTTP_PORT", "8080")),
        "token": os.environ.get("ICONA_TOKEN", ""),
        "password": os.environ.get("ICONA_PASSWORD", ""),
        "rtsp_port": int(os.environ.get("ICONA_RTSP_PORT", "8557")),
        "api_port": int(os.environ.get("ICONA_API_PORT", "8099")),
        "stream_path": os.environ.get("ICONA_STREAM_PATH", "live"),
        "auto_start_on_rtsp": bool(os.environ.get("ICONA_AUTO_START", "1") != "0"),
        "auto_start_on_ring": bool(os.environ.get("ICONA_AUTO_START_ON_RING", "1") != "0"),
        "enable_vip_listener": bool(os.environ.get("ICONA_VIP_LISTENER", "1") != "0"),
        "log_level": os.environ.get("ICONA_LOG_LEVEL", "info"),
        "model": os.environ.get("ICONA_MODEL", "6741W"),
    }


class IconaBridgeService:
    """Keep ICONA auth/config + VIP listener + optional video session + RTSP."""

    def __init__(self, opts: dict[str, Any]) -> None:
        self.opts = opts
        self.host: str = opts["host"]
        self.port: int = int(opts.get("port", 64100))
        self.http_port: int = int(opts.get("http_port", 8080))
        self.rtsp_port: int = int(opts.get("rtsp_port", 8557))
        self.bind_host: str = str(opts.get("bind_host", "0.0.0.0"))
        self.auto_start_on_rtsp: bool = bool(opts.get("auto_start_on_rtsp", True))
        self.auto_start_on_ring: bool = bool(opts.get("auto_start_on_ring", True))
        self.enable_vip_listener: bool = bool(opts.get("enable_vip_listener", True))
        self.model: str = str(opts.get("model", "6741W"))
        self.token: str = (opts.get("token") or "").strip()
        self.password: str = (opts.get("password") or "").strip()
        self.client: IconaBridgeClient | None = None
        self.device_config = None
        self.rtsp: LocalRtspServer | None = None
        self.session: VideoCallSession | None = None
        self._vip: VipEventListener | None = None
        self._ctpp_init_ts: int = 0
        self._session_lock = asyncio.Lock()
        self._connected = False
        self.last_error: str | None = None
        self._events: deque[dict[str, Any]] = deque(maxlen=50)
        self._ringing = False
        self._last_ring: dict[str, Any] | None = None
        self._pending_inbound: tuple[str, int] | None = None  # entrance, ring_ts
        self._ring_task: asyncio.Task[None] | None = None

    @property
    def rtsp_url(self) -> str:
        host = "127.0.0.1" if self.bind_host in ("0.0.0.0", "::") else self.bind_host
        return f"rtsp://{host}:{self.rtsp_port}/intercom"

    @property
    def status(self) -> dict[str, Any]:
        media = {}
        if self.session and self.session.rtp_receiver:
            rx = self.session.rtp_receiver
            media = {
                "udp_packets": rx.udp_media_packet_count,
                "tcp_packets": rx.tcp_media_packet_count,
            }
        return {
            "host": self.host,
            "port": self.port,
            "model": self.model,
            "connected": self._connected and bool(self.client and self.client.connected),
            "vip_listener": self._vip is not None,
            "video_active": self.session is not None and bool(getattr(self.session, "active", False)),
            "ringing": self._ringing,
            "last_ring": self._last_ring,
            "pending_inbound": bool(self._pending_inbound),
            "rtsp_url": self.rtsp_url,
            "rtsp_port": self.rtsp_port,
            "stream_path": "intercom",
            "has_token": bool(self.token),
            "doors": [d.name for d in (self.device_config.doors if self.device_config else [])],
            "apt_address": getattr(self.device_config, "apt_address", "") if self.device_config else "",
            "entrance_address": getattr(self.device_config, "caller_address", "") if self.device_config else "",
            "media": media,
            "last_error": self.last_error,
            "recent_events": list(self._events)[-10:],
        }

    def _record_event(self, event_type: str, **extra: Any) -> None:
        evt = {"type": event_type, "ts": time.time(), **extra}
        self._events.append(evt)
        LOG.info("Event %s %s", event_type, extra)

    async def resolve_token(self) -> str:
        if self.token:
            return self.token
        if not self.password:
            raise TokenExtractionError(
                "Missing credentials: set add-on option 'token' (32-char hex ICONA "
                "user-token) OR 'password' (device web UI password on :8080 used to "
                "extract the token from a configuration backup)."
            )
        LOG.info("Extracting ICONA token via device web UI backup on %s:%s", self.host, self.http_port)
        token = await extract_token(self.host, self.password, self.http_port)
        if not token:
            raise TokenExtractionError("Token extraction returned empty token")
        self.token = token
        LOG.info("Token extracted (%s…%s)", token[:4], token[-4:])
        return token

    async def connect(self) -> None:
        token = await self.resolve_token()
        client = IconaBridgeClient(self.host, self.port)
        await client.connect()
        await authenticate(client, token)
        config = await get_device_config(client)
        self.client = client
        self.device_config = config
        self._connected = True
        self.last_error = None
        client.set_disconnect_callback(self._on_disconnect)
        LOG.info(
            "ICONA connected host=%s model=%s apt=%s entrance=%s doors=%d",
            self.host,
            self.model,
            config.apt_address,
            config.caller_address,
            len(config.doors),
        )
        if self.enable_vip_listener:
            await self._start_vip_listener()

    def _on_disconnect(self) -> None:
        LOG.warning("ICONA TCP dropped unexpectedly")
        self._connected = False
        self._vip = None
        self.last_error = "tcp_disconnected"

    async def _start_vip_listener(self) -> None:
        assert self.client is not None
        assert self.device_config is not None
        # Stop previous listener task if any
        if self._vip is not None:
            with contextlib.suppress(Exception):
                await self._vip.stop()
            self._vip = None

        cfg = self.device_config
        our_addr = f"{cfg.apt_address}{cfg.apt_subaddress}"
        ctpp = self.client.get_channel("CTPP")
        if ctpp is None:
            ctpp = await self.client.open_channel("CTPP", ChannelType.UAUT, extra_data=our_addr)
            if self.client.get_channel("CSPB") is None:
                await self.client.open_channel("CSPB", ChannelType.UAUT)
            self._ctpp_init_ts = int(time.time()) & 0xFFFFFFFF
            await ctpp_init_sequence(
                self.client,
                ctpp,
                cfg.apt_address,
                cfg.apt_subaddress,
                our_addr,
                self._ctpp_init_ts,
            )
        elif self._ctpp_init_ts == 0:
            self._ctpp_init_ts = int(time.time()) & 0xFFFFFFFF

        def _on_push(event: PushEvent) -> None:
            self._record_event(event.event_type, apt_address=event.apt_address)
            if event.event_type == "ring":
                self._ringing = True
                self._last_ring = {
                    "ts": event.timestamp,
                    "apt_address": event.apt_address,
                }

        def _on_inbound_ring(entrance_addr: str, ring_ts: int) -> None:
            self._pending_inbound = (entrance_addr, ring_ts)
            self._ringing = True
            self._last_ring = {
                "ts": time.time(),
                "ring_ts": ring_ts,
                "entrance": entrance_addr,
            }
            self._record_event("ring", entrance=entrance_addr, ring_ts=ring_ts)
            if self.auto_start_on_ring and (self._ring_task is None or self._ring_task.done()):
                self._ring_task = asyncio.create_task(self._auto_inbound(entrance_addr, ring_ts))

        self._vip = VipEventListener(
            self.client,
            cfg,
            callback=_on_push,
            init_ts=self._ctpp_init_ts,
            on_inbound_ring=_on_inbound_ring,
        )
        await self._vip.start()
        LOG.info("VIP listener active (doorbell rings on CTPP)")

    async def _auto_inbound(self, entrance_addr: str, ring_ts: int) -> None:
        try:
            await self.start_inbound(entrance_addr, ring_ts)
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"auto_inbound: {exc}"
            LOG.exception("Auto inbound video on ring failed")

    async def ensure_rtsp(self) -> None:
        if self.rtsp is not None:
            return
        self.rtsp = LocalRtspServer(bind_host=self.bind_host, port=self.rtsp_port)
        await self.rtsp.start()
        LOG.info("Local RTSP listening on %s", self.rtsp_url)

    async def _ensure_connected(self) -> None:
        needs_connect = (
            self.client is None
            or self.device_config is None
            or not getattr(self.client, "connected", False)
        )
        if needs_connect:
            if self.client is not None:
                with contextlib.suppress(Exception):
                    if self._vip is not None:
                        await self._vip.stop()
                    await self.client.disconnect()
                self.client = None
                self._vip = None
                self._connected = False
            await self.connect()

    async def start_video(self) -> dict[str, Any]:
        """Outbound live view (HA-initiated, no doorbell ring required)."""
        async with self._session_lock:
            if self.session and self.session.active:
                return {"ok": True, "already": True, **self.status}
            await self._ensure_connected()
            assert self.client is not None
            assert self.device_config is not None
            # Pause VIP listen task so video owns CTPP reads; keep channels.
            if self._vip is not None:
                await self._vip.stop_task()
            # Drop stale VIP renewals so outbound call_init reads clean responses.
            ctpp = self.client.get_channel("CTPP")
            if ctpp is not None:
                while not ctpp.response_queue.empty():
                    try:
                        ctpp.response_queue.get_nowait()
                    except Exception:
                        break
            await self.ensure_rtsp()
            session = VideoCallSession(
                self.client,
                self.device_config,
                auto_timeout=True,
                rtsp_server=self.rtsp,
                on_call_end=self._on_call_end,
                on_ring=self._on_mid_call_ring,
            )
            await session.start()
            self.session = session
            self.last_error = None
            self._record_event("video_started", mode="outbound")
            LOG.info("Video session started → %s", self.rtsp_url)
            return {"ok": True, **self.status}

    async def start_inbound(self, entrance_addr: str | None = None, ring_ts: int | None = None) -> dict[str, Any]:
        """Passive inbound video after a doorbell ring (other phones still ring)."""
        async with self._session_lock:
            if self.session and self.session.active:
                return {"ok": True, "already": True, **self.status}
            await self._ensure_connected()
            assert self.client is not None
            assert self.device_config is not None
            if entrance_addr is None or ring_ts is None:
                if not self._pending_inbound:
                    raise ComelitError("No pending inbound ring — wait for doorbell or pass entrance/ring_ts")
                entrance_addr, ring_ts = self._pending_inbound
            if self._vip is not None:
                await self._vip.stop_task()
            await self.ensure_rtsp()
            renewal = (self._ctpp_init_ts + 0x01010000) & 0xFFFFFFFF
            session = VideoCallSession(
                self.client,
                self.device_config,
                auto_timeout=True,
                rtsp_server=self.rtsp,
                on_call_end=self._on_call_end,
                on_ring=self._on_mid_call_ring,
            )
            await session.start_inbound(entrance_addr, ring_ts, renewal_ack_ts=renewal)
            self.session = session
            self.last_error = None
            self._record_event("video_started", mode="inbound", entrance=entrance_addr)
            return {"ok": True, **self.status}

    async def answer(self) -> dict[str, Any]:
        """Answer / talk path.

        If a ring is pending and no session: start inbound then answer.
        If a passive inbound session is active: answer_inbound (opens audio TX).
        If an outbound session is active: answer peer sequence already runs after
        first frame; this is a no-op success.
        """
        async with self._session_lock:
            await self._ensure_connected()
            if self.session is None or not self.session.active:
                # Need inbound first
                pass
            else:
                await self.session.answer_inbound()
                self._ringing = False
                self._pending_inbound = None
                self._record_event("answered")
                return {"ok": True, **self.status}

        # Outside lock for start_inbound which takes the lock
        if self._pending_inbound:
            entrance, ring_ts = self._pending_inbound
            await self.start_inbound(entrance, ring_ts)
        elif self.session is None or not self.session.active:
            # No ring — start outbound live then rely on answer sequence
            await self.start_video()
            return {"ok": True, "note": "outbound_live_no_ring", **self.status}

        async with self._session_lock:
            if self.session and self.session.active:
                await self.session.answer_inbound()
                self._ringing = False
                self._pending_inbound = None
                self._record_event("answered")
            return {"ok": True, **self.status}

    def _on_mid_call_ring(self, entrance_addr: str, ring_ts: int) -> None:
        self._pending_inbound = (entrance_addr, ring_ts)
        self._ringing = True
        self._last_ring = {"ts": time.time(), "ring_ts": ring_ts, "entrance": entrance_addr}
        self._record_event("ring", entrance=entrance_addr, ring_ts=ring_ts, mid_call=True)

    def _on_call_end(self) -> None:
        LOG.info("Video session ended")
        self.session = None
        self._record_event("video_stopped")
        # Resume VIP listener on shared CTPP
        if self.enable_vip_listener and self.client and self.client.connected:
            asyncio.create_task(self._resume_vip())

    async def _resume_vip(self) -> None:
        try:
            await self._start_vip_listener()
        except Exception:  # noqa: BLE001
            LOG.exception("Failed to resume VIP listener after video")

    async def stop_video(self) -> dict[str, Any]:
        async with self._session_lock:
            if self.session is not None:
                await self.session.stop()
                self.session = None
            self._ringing = False
            self._record_event("video_stopped")
            if self.enable_vip_listener and self.client and self.client.connected:
                asyncio.create_task(self._resume_vip())
            return {"ok": True, **self.status}

    async def open_named_door(self, name: str | None = None) -> dict[str, Any]:
        await self._ensure_connected()
        assert self.client is not None
        assert self.device_config is not None
        doors = self.device_config.doors
        if not doors:
            raise ComelitError("No doors in device config")
        door = None
        if name:
            for d in doors:
                if d.name.lower() == name.lower():
                    door = d
                    break
            if door is None:
                raise ComelitError(f"Door not found: {name}")
        else:
            door = doors[0]
        # Prefer during-video CTPP open when a session is active
        if self.session and self.session.active:
            our = f"{self.device_config.apt_address}{self.device_config.apt_subaddress}"
            entrance = self.device_config.caller_address or our
            await self.session.async_open_door_on_ctpp(our, entrance, door.output_index or door.index)
        else:
            await open_door(self.host, self.port, self.token, self.client, self.device_config, door)
        self._record_event("door_opened", door=door.name)
        return {"ok": True, "door": door.name, **self.status}

    async def shutdown(self) -> None:
        await self.stop_video()
        if self._vip is not None:
            with contextlib.suppress(Exception):
                await self._vip.stop()
            self._vip = None
        if self.rtsp is not None:
            await self.rtsp.stop()
            self.rtsp = None
        if self.client is not None:
            await self.client.disconnect()
            self.client = None
        self._connected = False


def build_app(svc: IconaBridgeService) -> web.Application:
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, **svc.status})

    async def status(_: web.Request) -> web.Response:
        return web.json_response(svc.status)

    async def events(_: web.Request) -> web.Response:
        return web.json_response({"events": list(svc._events), "ringing": svc._ringing})

    async def start(_: web.Request) -> web.Response:
        try:
            result = await svc.start_video()
            return web.json_response(result)
        except ComelitError as exc:
            svc.last_error = str(exc)
            LOG.exception("start_video failed")
            return web.json_response({"ok": False, "error": str(exc), **svc.status}, status=500)

    async def stop(_: web.Request) -> web.Response:
        result = await svc.stop_video()
        return web.json_response(result)

    async def answer(_: web.Request) -> web.Response:
        try:
            result = await svc.answer()
            return web.json_response(result)
        except ComelitError as exc:
            svc.last_error = str(exc)
            LOG.exception("answer failed")
            return web.json_response({"ok": False, "error": str(exc), **svc.status}, status=500)

    async def door(request: web.Request) -> web.Response:
        try:
            name = request.query.get("name") or request.query.get("door")
            if request.can_read and request.content_type == "application/json":
                body = await request.json()
                name = body.get("name") or body.get("door") or name
            result = await svc.open_named_door(name)
            return web.json_response(result)
        except ComelitError as exc:
            svc.last_error = str(exc)
            LOG.exception("door open failed")
            return web.json_response({"ok": False, "error": str(exc), **svc.status}, status=500)

    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/status", status)
    app.router.add_get("/events", events)
    app.router.add_post("/start", start)
    app.router.add_post("/stop", stop)
    app.router.add_post("/answer", answer)
    app.router.add_post("/door", door)
    app.router.add_get("/start", start)
    app.router.add_get("/stop", stop)
    app.router.add_get("/answer", answer)
    app.router.add_get("/door", door)
    return app


async def amain() -> None:
    opts = load_options()
    level = str(opts.get("log_level", "info")).upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    svc = IconaBridgeService(opts)
    api_port = int(opts.get("api_port", 8099))

    await svc.ensure_rtsp()

    try:
        await svc.connect()
    except Exception as exc:  # noqa: BLE001 — surface in /status for operators
        svc.last_error = str(exc)
        LOG.error("Initial ICONA connect failed: %s", exc)

    app = build_app(svc)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", api_port)
    await site.start()
    LOG.info(
        "Control API on http://0.0.0.0:%s (POST /start /stop /answer /door, GET /status /events)",
        api_port,
    )

    stop_event = asyncio.Event()

    def _stop(*_: Any) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib_suppress():
            loop.add_signal_handler(sig, _stop)

    await stop_event.wait()
    await svc.shutdown()
    await runner.cleanup()


class contextlib_suppress:
    """Tiny helper so signal handlers don't crash on Windows."""

    def __enter__(self) -> contextlib_suppress:
        return self

    def __exit__(self, *exc: object) -> bool:
        return True


if __name__ == "__main__":
    asyncio.run(amain())
