"""Kontent: 'Batafsil nazariya' fayllari tuzilmasi va hajmi."""
import re
from pathlib import Path

import pytest
import yaml

from src.services.theory import CHUNK_LIMIT, theory_messages

ROOT = Path(__file__).resolve().parents[1]
THEORY = ROOT / "content" / "junior" / "theory"
SECTIONS = ["Tushuncha", "Qanday ishlaydi", "Buyruqlar", "Odatiy xatolar", "Intervyuda"]
FILES = sorted(THEORY.glob("*.md"))


def linux_basics_keys() -> list[str]:
    data = yaml.safe_load((ROOT / "content" / "junior" / "01-linux-basics.yaml").read_text(encoding="utf-8"))
    return [lesson["key"] for lesson in data["lessons"]]


def test_linux_basics_pilot_is_complete():
    assert {p.stem for p in FILES} >= set(linux_basics_keys())


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_structure_and_size(path: Path):
    text = path.read_text(encoding="utf-8")
    assert re.findall(r"^## (.+)$", text, flags=re.M) == SECTIONS
    words = len(text.split())
    assert 900 <= words <= 1400, words
    assert text.count("```") % 2 == 0  # yopilmagan kod bloki yo'q
    assert all(len(m) <= CHUNK_LIMIT for m in theory_messages(text, header="📖 <b>Batafsil nazariya</b>"))
