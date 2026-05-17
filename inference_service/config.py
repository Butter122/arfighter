"""Configuration for the inference service."""

from pathlib import Path

# -- Paths (relative to this file's directory)
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

BEST_MODEL_PATH = PROJECT_ROOT / "skeleton_action" / "models" / "best_model.pth"
SCALER_PATH = PROJECT_ROOT / "skeleton_action" / "data" / "processed" / "scaler.pkl"

# -- Model settings (must match training config)
SEQUENCE_LENGTH: int = 30
INPUT_SIZE: int = 132
HIDDEN_SIZE: int = 128
NUM_LAYERS: int = 2
NUM_CLASSES: int = 6
DROPOUT: float = 0.3

ACTION_CLASSES: dict[int, str] = {
    0: "idle",
    1: "punch_left",
    2: "punch_right",
    3: "kick",
    4: "block",
    5: "jump",
}

# -- Server
INFERENCE_PORT: int = 8001
GAME_SERVER_WS: str = "ws://localhost:8000/ws"
INFERENCE_EVERY_N_FRAMES: int = 5

# -- MediaPipe
MIN_DETECTION_CONFIDENCE: float = 0.5
MIN_TRACKING_CONFIDENCE: float = 0.5
