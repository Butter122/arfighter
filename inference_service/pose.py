"""MediaPipe Pose wrapper for single-frame keypoint extraction."""

from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np

from config import MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE


class PoseExtractor:
    """Wraps MediaPipe Pose for extracting 132-D keypoint vectors from images."""

    def __init__(self) -> None:
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

    def extract(self, frame_bytes: bytes) -> np.ndarray | None:
        """Extract a (132,) keypoint vector from JPEG-encoded image bytes.

        Args:
            frame_bytes: Raw JPEG bytes of a single frame.

        Returns:
            Float32 array of shape (132,) or None if no pose detected.
        """
        arr = np.frombuffer(frame_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._pose.process(rgb)
        rgb.flags.writeable = True

        if not results.pose_landmarks:
            return None

        landmarks = np.array(
            [
                [lm.x, lm.y, lm.z, lm.visibility]
                for lm in results.pose_landmarks.landmark
            ],
            dtype=np.float32,
        ).flatten()
        return landmarks

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._pose.close()
