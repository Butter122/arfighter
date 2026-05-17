"""FastAPI WebSocket server for the fighting game.

Accepts two player connections and broadcasts game state updates.

Usage:
    uvicorn server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from game import GameState

app = FastAPI(title="Fighting Game Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game = GameState()
connections: dict[str, WebSocket] = {}
last_actions: dict[str, str] = {"p1": "idle", "p2": "idle"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()

    # Assign player slot
    if "p1" not in connections:
        player_id = "p1"
    elif "p2" not in connections:
        player_id = "p2"
    else:
        player_id = "spectator"

    connections[player_id] = ws

    try:
        await ws.send_text(json.dumps({"type": "welcome", "player_id": player_id}))

        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if player_id in ("p1", "p2"):
                action = msg.get("action", "idle")
                last_actions[player_id] = action

                state = game.update(last_actions["p1"], last_actions["p2"])

                if game.get_winner():
                    await _broadcast(state)
                    game.reset()
                    last_actions = {"p1": "idle", "p2": "idle"}
                    continue

                await _broadcast(state)

    except WebSocketDisconnect:
        pass
    finally:
        connections.pop(player_id, None)
        if player_id in ("p1", "p2"):
            game.reset()
            last_actions[player_id] = "idle"
            await _broadcast({"type": "reset", "reason": f"{player_id} disconnected"})


async def _broadcast(message: dict) -> None:
    """Send a JSON message to all connected clients."""
    payload = json.dumps(message)
    for ws in list(connections.values()):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
