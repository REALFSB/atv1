import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from src.ingest import SyntheticSource, load_operations


@pytest.fixture(scope="session")
def ops():
    return load_operations(SyntheticSource(n_employees=60, n_days=40))
