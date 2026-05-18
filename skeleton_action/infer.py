"""Real-time action recognition from webcam using a trained model.

Usage:
    python infer.py
"""

from __future__ import annotations

import pickle
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
import torch

from config import (
    ACTION_CLASSES,
    BEST_MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    INFERENCE_EVERY_N_FRAMES,
    INPUT_SIZE,
    SCALER_PATH,
    SEQUENCE_LENGTH,
)
from model import ActionLSTM


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load model
    model = ActionLSTM(num_classes=len(ACTION_CLASSES))
    model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()

    # Load scaler
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam. Check that it is connected and not in use.")
        return

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    buffer: deque[np.ndarray] = deque(maxlen=SEQUENCE_LENGTH)
    predicted_label: str = ""
    confidence: float = 0.0
    frame_count: int = 0
    fps: float = 0.0
    fps_timer = time.time()

    print("Running inference. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = pose.process(rgb)
        rgb.flags.writeable = True

        frame_count += 1

        # FPS update every second
        if time.time() - fps_timer >= 1.0:
            fps = frame_count / (time.time() - fps_timer)
            frame_count = 0
            fps_timer = time.time()

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),
            )

            lm = np.array(
                [
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in results.pose_landmarks.landmark
                ],
                dtype=np.float32,
            ).flatten()
            buffer.append(lm)
        else:
            buffer.clear()

        # Run inference every N frames when buffer is full
        if (
            len(buffer) == SEQUENCE_LENGTH
            and frame_count % INFERENCE_EVERY_N_FRAMES == 0
        ):
            seq = np.stack(list(buffer), axis=0)  # (30, 132)
            seq_norm = scaler.transform(seq)
            inp = torch.from_numpy(seq_norm).float().unsqueeze(0).to(device)  # (1,30,132)

            with torch.no_grad():
                logits = model(inp)
                probs = torch.softmax(logits, dim=1)
                top_prob, top_idx = probs.max(dim=1)
                confidence = top_prob.item()
                if confidence < CONFIDENCE_THRESHOLD:
                    predicted_label = "idle"
                else:
                    predicted_label = ACTION_CLASSES.get(int(top_idx.item()), "?")

        # HUD
        if predicted_label:
            text = f"{predicted_label} ({confidence * 100:.1f}%)"
            cv2.putText(
                frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3
            )
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (frame.shape[1] - 150, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        cv2.imshow("Inference", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    pose.close()


if __name__ == "__main__":
    main()
