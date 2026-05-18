"""LSTM model for skeleton-based action recognition."""

from __future__ import annotations

import torch.nn as nn


class ActionLSTM(nn.Module):
    """Two-layer LSTM for classifying 30-frame skeleton sequences.

    Input shape:  (batch, 30, 132) — 33 landmarks × 4 features each.
    Output shape: (batch, 4)      — logits over 4 action classes (plus idle fallback).
    """

    def __init__(
        self,
        input_size: int = 132,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 4,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":  # noqa: F821
        """Forward pass.

        Args:
            x: Float tensor of shape (batch_size, 30, 132).

        Returns:
            Float tensor of shape (batch_size, num_classes).
        """
        # lstm_out: (batch, seq_len, hidden)
        lstm_out, _ = self.lstm(x)
        # Use the last timestep's output for classification
        last_out = lstm_out[:, -1, :]
        return self.fc(last_out)
