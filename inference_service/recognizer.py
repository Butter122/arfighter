"""LSTM-based action recognizer with per-player rolling buffers."""

from __future__ import annotations

import pickle
from collections import deque

import numpy as np
import torch

from config import (
    ACTION_CLASSES,
    BEST_MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    INFERENCE_EVERY_N_FRAMES,
    INPUT_SIZE,
    HIDDEN_SIZE,
    NUM_CLASSES,
    NUM_LAYERS,
    DROPOUT,
    SCALER_PATH,
    SEQUENCE_LENGTH,
)

# Import the model class from the sibling project
import sys
sys.path.insert(0, str(BEST_MODEL_PATH.parents[2]))
from skeleton_action.model import ActionLSTM  # type: ignore[import-untyped]


class ActionRecognizer:
    """Maintains rolling keypoint buffers per player and runs LSTM inference."""

    def __init__(self) -> None:
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model = ActionLSTM(
            input_size=INPUT_SIZE,
            hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS,
            num_classes=NUM_CLASSES,
            dropout=DROPOUT,
        )
        self._model.load_state_dict(
            torch.load(BEST_MODEL_PATH, map_location=self._device)
        )
        self._model.to(self._device)
        self._model.eval()

        with open(SCALER_PATH, "rb") as f:
            self._scaler = pickle.load(f)

        self._buffers: dict[str, deque[np.ndarray]] = {}
        self._frame_counts: dict[str, int] = {}

    def update(self, player_id: str, keypoints: np.ndarray) -> tuple[str, float] | None:
        """Push a keypoint frame and return a prediction when ready.

        Args:
            player_id: "p1" or "p2".
            keypoints: Float32 array of shape (132,).

        Returns:
            (action_label, confidence) tuple or None if buffer not full or
            not an inference frame.
        """
        buf = self._buffers.setdefault(player_id, deque(maxlen=SEQUENCE_LENGTH))
        buf.append(keypoints)
        self._frame_counts[player_id] = self._frame_counts.get(player_id, 0) + 1

        if len(buf) < SEQUENCE_LENGTH:
            return None
        if self._frame_counts[player_id] % INFERENCE_EVERY_N_FRAMES != 0:
            return None

        seq = np.stack(list(buf), axis=0)
        seq_norm = self._scaler.transform(seq)
        inp = (
            torch.from_numpy(seq_norm).float().unsqueeze(0).to(self._device)
        )

        with torch.no_grad():
            logits = self._model(inp)
            probs = torch.softmax(logits, dim=1)
            top_prob, top_idx = probs.max(dim=1)

        conf = float(top_prob.item())
        if conf < CONFIDENCE_THRESHOLD:
            return "idle", conf
        label = ACTION_CLASSES.get(int(top_idx.item()), "idle")
        return label, conf
