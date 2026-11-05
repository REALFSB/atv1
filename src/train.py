"""Compatibility entry point for model training."""

from .ml.train import (
    MODEL_REGISTRY,
    TARGET_AUC,
    TARGET_RECALL,
    TrainResult,
    main,
    meets_targets,
    register_model,
    save_artifacts,
    time_split,
    train_model,
)

__all__ = [
    "MODEL_REGISTRY",
    "TARGET_AUC",
    "TARGET_RECALL",
    "TrainResult",
    "main",
    "meets_targets",
    "register_model",
    "save_artifacts",
    "time_split",
    "train_model",
]

if __name__ == "__main__":
    main()
