"""Train the ActionLSTM model on processed skeleton data.

Usage:
    python train.py
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader, TensorDataset

from config import (
    ACTION_CLASSES,
    BEST_MODEL_PATH,
    BATCH_SIZE,
    INPUT_SIZE,
    HIDDEN_SIZE,
    LEARNING_RATE,
    MODEL_DIR,
    NUM_CLASSES,
    NUM_EPOCHS,
    NUM_LAYERS,
    DROPOUT,
    X_TRAIN_PATH,
    X_VAL_PATH,
    Y_TRAIN_PATH,
    Y_VAL_PATH,
)
from model import ActionLSTM


def load_data() -> tuple[TensorDataset, TensorDataset]:
    """Load preprocessed splits and wrap in TensorDatasets."""
    X_train = torch.from_numpy(np.load(X_TRAIN_PATH)).float()
    X_val = torch.from_numpy(np.load(X_VAL_PATH)).float()
    y_train = torch.from_numpy(np.load(Y_TRAIN_PATH)).long()
    y_val = torch.from_numpy(np.load(Y_VAL_PATH)).long()
    return (
        TensorDataset(X_train, y_train),
        TensorDataset(X_val, y_val),
    )


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    """Compute classification accuracy given logits and targets."""
    preds = logits.argmax(dim=1)
    return (preds == targets).float().mean().item()


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_ds, val_ds = load_data()
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    model = ActionLSTM(
        input_size=INPUT_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        num_classes=NUM_CLASSES,
        dropout=DROPOUT,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_val_acc: float = 0.0
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, NUM_EPOCHS + 1):
        # ---- train ----
        model.train()
        total_loss, total_acc, n_batches = 0.0, 0.0, 0
        for Xb, yb in train_loader:
            Xb, yb = Xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(Xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            total_acc += accuracy(logits, yb)
            n_batches += 1

        train_loss = total_loss / n_batches
        train_acc = total_acc / n_batches

        # ---- val ----
        model.eval()
        val_acc_total, val_n = 0.0, 0
        with torch.no_grad():
            for Xb, yb in val_loader:
                Xb, yb = Xb.to(device), yb.to(device)
                logits = model(Xb)
                val_acc_total += accuracy(logits, yb) * Xb.size(0)
                val_n += Xb.size(0)
        val_acc = val_acc_total / val_n

        print(
            f"Epoch {epoch:3d}  |  loss: {train_loss:.4f}  "
            f"train_acc: {train_acc:.4f}  val_acc: {val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), BEST_MODEL_PATH)

    # ---- final evaluation ----
    print(f"\nBest val_acc: {best_val_acc:.4f}")
    model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
    model.eval()

    all_preds: list[int] = []
    all_labels: list[int] = []
    with torch.no_grad():
        for Xb, yb in val_loader:
            Xb = Xb.to(device)
            preds = model(Xb).argmax(dim=1).cpu().numpy()
            all_preds.extend(preds.tolist())
            all_labels.extend(yb.numpy().tolist())

    target_names = [ACTION_CLASSES[i] for i in range(NUM_CLASSES)]
    print("\n" + classification_report(all_labels, all_preds, target_names=target_names,
                                        zero_division=0))


if __name__ == "__main__":
    main()
