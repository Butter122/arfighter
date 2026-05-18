"""Build train/val splits from raw skeleton recordings.

Usage:
    python preprocess.py
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config import (
    ACTION_CLASSES,
    INPUT_SIZE,
    PROCESSED_DIR,
    RANDOM_SEED,
    RAW_DIR,
    SCALER_PATH,
    SEQUENCE_LENGTH,
    VAL_SPLIT,
    X_TRAIN_PATH,
    X_VAL_PATH,
    Y_TRAIN_PATH,
    Y_VAL_PATH,
)

# Maps raw directory names → label index (punch_left + punch_right both → punch)
DIR_TO_LABEL: dict[str, int] = {
    "punch_left": 0,
    "punch_right": 0,
    "punch": 0,
    "kick": 1,
    "block": 2,
    "ranged_attack": 3,
}


def load_raw_data() -> tuple[np.ndarray, np.ndarray]:
    """Load all .npy files from data/raw/ and return X, y arrays.

    punch_left and punch_right are merged into a single "punch" label.
    Directories not in DIR_TO_LABEL (idle, jump, etc.) are silently skipped.
    """
    X_list: list[np.ndarray] = []
    y_list: list[int] = []

    action_dirs = sorted(
        d for d in RAW_DIR.iterdir() if d.is_dir() and d.name in DIR_TO_LABEL
    )
    if not action_dirs:
        raise FileNotFoundError(
            f"No recognised action directories found in {RAW_DIR}. "
            f"Expected: {sorted(set(DIR_TO_LABEL.keys()))}. Run collect.py first."
        )

    for action_dir in action_dirs:
        label = DIR_TO_LABEL[action_dir.name]
        npy_files = sorted(action_dir.glob("*.npy"))
        if not npy_files:
            print(f"  Warning: no .npy files in {action_dir}")
            continue
        for fp in npy_files:
            arr = np.load(fp)
            if arr.shape != (SEQUENCE_LENGTH, INPUT_SIZE):
                print(f"  Warning: skipping {fp}, unexpected shape {arr.shape}")
                continue
            X_list.append(arr)
            y_list.append(label)
        print(f"  {action_dir.name}: {len(npy_files)} samples → label {label}")

    if not X_list:
        raise ValueError("No valid samples found. Check data/raw/ contents.")

    X = np.stack(X_list, axis=0).astype(np.float32)
    y = np.array(y_list, dtype=np.int64)
    return X, y


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading raw data...")
    X, y = load_raw_data()
    print(f"Total samples: {len(y)}")

    # Train/val split (stratified)
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=VAL_SPLIT,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    # Flatten for scaler: (N, 30, 132) -> (N*30, 132), then reshape back
    n_train, seq_len, feat_dim = X_train.shape
    X_train_flat = X_train.reshape(-1, feat_dim)
    scaler = StandardScaler()
    scaler.fit(X_train_flat)
    X_train_norm = scaler.transform(X_train_flat).reshape(n_train, seq_len, feat_dim)

    n_val = X_val.shape[0]
    X_val_norm = scaler.transform(X_val.reshape(-1, feat_dim)).reshape(n_val, seq_len, feat_dim)

    # Save
    np.save(X_TRAIN_PATH, X_train_norm)
    np.save(X_VAL_PATH, X_val_norm)
    np.save(Y_TRAIN_PATH, y_train)
    np.save(Y_VAL_PATH, y_val)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # Class distribution
    def class_dist(y_arr: np.ndarray, tag: str) -> None:
        unique, counts = np.unique(y_arr, return_counts=True)
        print(f"\n{tag} distribution:")
        for lbl, cnt in zip(unique, counts):
            print(f"  {ACTION_CLASSES[int(lbl)]} ({lbl}): {cnt}")

    class_dist(y_train, "Train")
    class_dist(y_val, "Val")
    print("\nDone. Processed data saved to", PROCESSED_DIR)


if __name__ == "__main__":
    main()
