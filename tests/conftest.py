import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def ops():
    # import tardio: o commit base do histórico ainda não tem src/ingest.py
    from src.ingest import SyntheticSource, load_operations

    return load_operations(SyntheticSource(n_employees=60, n_days=40))
