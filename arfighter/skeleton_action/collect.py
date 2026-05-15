"""Record labeled skeleton sequences from webcam using MediaPipe Pose.

Usage:
    python collect.py --action punch_left --samples 100
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from config import ACTION_CLASSES, FEATURES_PER_LANDMARK, NUM_LANDMARKS, RAW_DIR, SEQUENCE_LENGTH


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Record skeleton sequences for action recognition."
    )
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=list(ACTION_CLASSES.values()),
        help="Action label to record.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=100,
        help="Number of samples to collect (default: 100).",
    )
    return parser.parse_args()


def draw_countdown(
    image: np.ndarray, seconds: int, color: tuple[int, int, int] = (0, 255, 0)
) -> None:
    """Draw a countdown number on the centre of the frame."""
    h, w = image.shape[:2]
    text = str(seconds)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 4, 8)
    cv2.putText(
        image,
        text,
        (w // 2 - tw // 2, h // 2 + th // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        4,
        color,
        8,
        cv2.LINE_AA,
    )


def draw_progress(
    image: np.ndarray, current: int, total: int, action: str
) -> None:
    """Draw a progress bar and count at the top of the frame."""
    text = f"Collected {current}/{total} for {action}"
    cv2.putText(
        image, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
    )


def main() -> None:
    args = parse_args()
    action_dir = RAW_DIR / args.action
    action_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam. Check that it is connected and not in use.")
        sys.exit(1)

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    print(f"Recording action: {args.action}  |  Samples: {args.samples}")
    print("Press SPACE to begin each sample, or 'q' to quit.\n")

    collected: int = 0
    recording: bool = False
    countdown_start: float = 0.0
    countdown_seconds: int = 3
    frames: list[np.ndarray] = []

    while collected < args.samples:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = pose.process(rgb)
        rgb.flags.writeable = True

        # Draw skeleton
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),
            )

        draw_progress(frame, collected, args.samples, args.action)

        if recording:
            elapsed = time.time() - countdown_start
            remaining = countdown_seconds - int(elapsed)

            if remaining > 0:
                draw_countdown(frame, remaining)
            else:
                if results.pose_landmarks:
                    lm = np.array(
                        [
                            [lm.x, lm.y, lm.z, lm.visibility]
                            for lm in results.pose_landmarks.landmark
                        ],
                        dtype=np.float32,
                    ).flatten()
                    frames.append(lm)
                else:
                    # No detection — fill with zeros so timing stays aligned
                    frames.append(np.zeros(NUM_LANDMARKS * FEATURES_PER_LANDMARK, dtype=np.float32))

                if len(frames) >= SEQUENCE_LENGTH:
                    ts = int(time.time() * 1000)
                    path = action_dir / f"{args.action}_{ts}.npy"
                    np.save(path, np.stack(frames, axis=0))
                    collected += 1
                    recording = False
                    frames.clear()
                    print(f"Collected {collected}/{args.samples} for {args.action}")

        cv2.imshow("Collect", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("\nQuit early.")
            break
        if key == ord(" ") and not recording:
            recording = True
            countdown_start = time.time()
            frames.clear()

    cap.release()
    cv2.destroyAllWindows()
    pose.close()
    print(f"Done. {collected} samples saved to {action_dir}")


if __name__ == "__main__":
    main()
