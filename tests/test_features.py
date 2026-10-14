import pandas as pd

from src.features import FEATURE_COLUMNS, add_features, build_preprocessor, feature_matrix


def test_add_features_is_pure_and_correct():
    df = pd.DataFrame({"overtime_hours": [10, 0], "weekly_hours": [40, 40], "satisfaction": [1.5, 4.0]})
    out = add_features(df)
    assert out["overtime_ratio"].tolist() == [0.25, 0.0]
    assert out["low_satisfaction"].tolist() == [1, 0]
    assert "overtime_ratio" not in df.columns  # entrada não é alterada


def test_protected_attributes_are_not_features():
    assert not {"age", "gender", "sick_days"} & set(FEATURE_COLUMNS)


def test_preprocessor_handles_all_feature_columns(ops):
    X = feature_matrix(ops)
    assert list(X.columns) == FEATURE_COLUMNS
    assert build_preprocessor().fit_transform(X).shape[0] == len(ops)
