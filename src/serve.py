"""Compatibility entry point for model serving."""

from .serving.risk import (
    BAND_HIGH,
    BAND_MEDIUM,
    Predictor,
    export_risk_csv,
    export_risk_js,
    load_model,
    main,
    predict_risk,
    risk_band,
    top_factors,
)

__all__ = [
    "BAND_HIGH",
    "BAND_MEDIUM",
    "Predictor",
    "export_risk_csv",
    "export_risk_js",
    "load_model",
    "main",
    "predict_risk",
    "risk_band",
    "top_factors",
]

if __name__ == "__main__":
    main()
