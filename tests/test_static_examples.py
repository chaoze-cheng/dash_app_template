"""Lightweight tests requiring no optional runtime dependencies."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_python_examples_parse():
    for path in (ROOT / "examples").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_each_example_has_readme():
    example_dirs = [p.parent for p in (ROOT / "examples").rglob("*.py")]
    assert example_dirs
    for folder in example_dirs:
        assert (folder / "README.md").exists(), folder
