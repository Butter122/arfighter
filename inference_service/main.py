"""FastAPI server that receives frames from Unity, runs pose + action inference.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from config import INFERENCE_PORT
from pose import PoseExtractor
from recognizer import ActionRecognizer
from client import GameServerClient

pose_extractor: PoseExtractor
recognizer: ActionRecognizer
game_client: GameServerClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pose_extractor, recognizer, game_client
    pose_extractor = PoseExtractor()
    recognizer = ActionRecognizer()
    game_client = GameServerClient()
    await game_client.start()
    yield
    await game_client.stop()
    pose_extractor.close()


app = FastAPI(title="Pose Inference Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/frame/{player_id}")
async def receive_frame(player_id: str, request: Request) -> Response:
    """Receive a JPEG frame from a player and run inference.

    If an action is recognized, it is forwarded to the game logic server.
    """
    frame_bytes = await request.body()

    # Run pose extraction in thread pool (synchronous OpenCV / MediaPipe)
    loop = asyncio.get_running_loop()
    keypoints = await loop.run_in_executor(None, pose_extractor.extract, frame_bytes)

    if keypoints is None:
        return JSONResponse({"action": None})

    # Run inference in thread pool (synchronous torch call)
    result = await loop.run_in_executor(
        None, _run_inference, player_id, keypoints
    )

    if result is None:
        return JSONResponse({"action": None})

    action, confidence = result
    # Fire-and-forget to game server
    asyncio.create_task(game_client.send_action(player_id, action))

    return JSONResponse({"action": action, "confidence": round(confidence, 4)})


def _run_inference(
    player_id: str, keypoints: "np.ndarray"  # type: ignore[name-defined]  # noqa: F821
) -> tuple[str, float] | None:
    """Synchronous wrapper for the recognizer update call."""
    return recognizer.update(player_id, keypoints)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=INFERENCE_PORT, reload=False)
