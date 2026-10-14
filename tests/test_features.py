import pandas as pd

from src.features import FEATURE_COLUMNS, add_features, build_preprocessor, feature_matrix


def test_add_features_is_pure_and_correct():
    df = pd.DataFrame({"date": ["2026-09-07", "2026-09-09"],  # segunda, quarta
                       "overtime_hours_week": [12.0, 3.0]})
    out = add_features(df)
    assert out["is_monday_or_friday"].tolist() == [1, 0]
    assert out["overtime_high"].tolist() == [1, 0]
    assert "day_of_week" not in df.columns  # entrada não é alterada


def test_preprocessor_handles_all_feature_columns(ops):
    X = feature_matrix(ops)
    assert list(X.columns) == FEATURE_COLUMNS
    assert build_preprocessor().fit_transform(X).shape[0] == len(ops)
