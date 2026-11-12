"""Checa a estrutura mínima do repositório (é o único teste do commit base,
para que o CI já rode verde antes do primeiro PR de história)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", [
    "README.md", "pyproject.toml", "requirements.txt", ".gitignore",
    ".github/workflows/tests.yml", ".github/pull_request_template.md",
    "docs/backlog.md", "docs/04-planejamento-e-riscos.md",
])
def test_required_project_files_exist(path):
    assert (ROOT / path).is_file()


def test_raw_data_is_not_versioned():
    assert "data/*" in (ROOT / ".gitignore").read_text(encoding="utf-8")
