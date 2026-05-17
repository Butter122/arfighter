"""Async WebSocket client that forwards recognized actions to the game server."""

from __future__ import annotations

import asyncio
import json

import websockets

from config import GAME_SERVER_WS


class GameServerClient:
    """Async WebSocket client connecting to the game_logic server.

    Auto-reconnects on failure. Queues messages when disconnected.
    """

    def __init__(self) -> None:
        self._ws: "websockets.WebSocketClientProtocol | None" = None
        self._running: bool = False
        self._task: "asyncio.Task[None] | None" = None
        self._pending: list[dict] = []

    async def start(self) -> None:
        """Begin the connection loop (non-blocking)."""
        self._running = True
        self._task = asyncio.create_task(self._connect_loop())

    async def stop(self) -> None:
        """Shut down the connection loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()

    async def send_action(self, player_id: str, action: str) -> None:
        """Send an action to the game server."""
        payload = {"player_id": player_id, "action": action}
        if self._ws and self._ws.open:
            try:
                await self._ws.send(json.dumps(payload))
                return
            except websockets.ConnectionClosed:
                pass
        # Queue for reconnect
        self._pending.append(payload)

    async def _connect_loop(self) -> None:
        while self._running:
            try:
                async with websockets.connect(GAME_SERVER_WS) as ws:
                    self._ws = ws
                    # Drain pending messages
                    while self._pending:
                        msg = self._pending.pop(0)
                        await ws.send(json.dumps(msg))
                    # Keep-alive: wait for server messages (we don't use them, but need to detect disconnect)
                    async for _ in ws:
                        pass
            except (OSError, websockets.ConnectionClosed):
                self._ws = None
                await asyncio.sleep(3)
