"""Validate basic repository structure without optional dependencies."""
from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
for path in (root / "examples").rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert (path.parent / "README.md").is_file(), path
print("All Python examples parse and contain README.md")
