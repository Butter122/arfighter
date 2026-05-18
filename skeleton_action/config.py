"""Global configuration for the skeleton action recognition pipeline."""

from pathlib import Path

# -- Project root
ROOT = Path(__file__).resolve().parent

# -- Data paths
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"

# -- Processed file names
X_TRAIN_PATH = PROCESSED_DIR / "X_train.npy"
X_VAL_PATH = PROCESSED_DIR / "X_val.npy"
Y_TRAIN_PATH = PROCESSED_DIR / "y_train.npy"
Y_VAL_PATH = PROCESSED_DIR / "y_val.npy"
SCALER_PATH = PROCESSED_DIR / "scaler.pkl"
BEST_MODEL_PATH = MODEL_DIR / "best_model.pth"

# -- Action classes
#   Model trains on 4 classes. "idle" is a fallback at inference time
#   when confidence is below the threshold.
ACTION_CLASSES: dict[int, str] = {
    0: "punch",
    1: "kick",
    2: "block",
    3: "ranged_attack",
}

NUM_CLASSES: int = len(ACTION_CLASSES)

# -- Sequence / data
SEQUENCE_LENGTH: int = 30
NUM_LANDMARKS: int = 33
FEATURES_PER_LANDMARK: int = 4  # x, y, z, visibility
INPUT_SIZE: int = NUM_LANDMARKS * FEATURES_PER_LANDMARK  # 132

# -- Train / val split
VAL_SPLIT: float = 0.2
RANDOM_SEED: int = 42

# -- Model architecture
HIDDEN_SIZE: int = 128
NUM_LAYERS: int = 2
DROPOUT: float = 0.3

# -- Training
BATCH_SIZE: int = 32
LEARNING_RATE: float = 1e-3
NUM_EPOCHS: int = 50

# -- Inference
INFERENCE_EVERY_N_FRAMES: int = 5
CONFIDENCE_THRESHOLD: float = 0.6  # below this → classified as "idle"
