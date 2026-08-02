"""Byte budgets against multi-byte text.

A budget counted in bytes behaves very differently for CJK authors: the same
limit holds roughly a third as many characters, and a cut can land inside a
character and corrupt it.
"""

from __future__ import annotations

from agents_doctor.config import Config
from agents_doctor.discovery import build_load_plan, read_instruction_file

JAPANESE = "日本語の指示です。"  # 9 characters, 3 bytes each in UTF-8


def test_japanese_costs_three_bytes_per_character(make_repo):
    root = make_repo({"AGENTS.md": JAPANESE})
    file = read_instruction_file(root / "AGENTS.md", root)
    assert file.char_count == 9
    assert file.raw_size == 27
    assert file.bytes_per_char == 3.0


def test_cut_inside_a_character_is_reported(make_repo):
    """A budget that ends mid-sequence corrupts the character it splits."""
    root = make_repo({"AGENTS.md": "ab", "sub/AGENTS.md": JAPANESE})
    # 2 bytes of ASCII, then 4 bytes leaves the second Japanese character split.
    plan = build_load_plan(root / "sub", root, Config(max_bytes=6))
    chunk = plan.chunks[1]
    assert chunk.truncated
    assert chunk.included_bytes == 4
    assert chunk.splits_character


def test_cut_on_a_character_boundary_is_not_reported_as_corrupt(make_repo):
    root = make_repo({"AGENTS.md": "ab", "sub/AGENTS.md": JAPANESE})
    # 2 + 3 bytes lands exactly on the boundary after one full character.
    plan = build_load_plan(root / "sub", root, Config(max_bytes=5))
    chunk = plan.chunks[1]
    assert chunk.truncated
    assert chunk.included_bytes == 3
    assert not chunk.splits_character


def test_ascii_is_never_reported_as_corrupt(make_repo, filler):
    root = make_repo({"AGENTS.md": filler(10)})
    plan = build_load_plan(root, root, Config(max_bytes=4))
    assert plan.chunks[0].truncated
    assert not plan.chunks[0].splits_character


def test_lost_characters_are_counted_not_just_bytes(make_repo):
    root = make_repo({"AGENTS.md": JAPANESE})
    plan = build_load_plan(root, root, Config(max_bytes=9))
    chunk = plan.chunks[0]
    assert chunk.lost_bytes == 18
    # Three characters survive; the author lost six of the nine they wrote.
    assert chunk.lost_chars == 6


def test_non_utf8_file_is_measured_in_bytes_not_guesses(make_repo):
    """A CP932 file still has a true byte size, which is what the budget counts.

    The loader decodes leniently, so the model receives replacement characters
    rather than the author's text. Byte accounting stays exact -- character counts
    necessarily do not, because the original characters are already gone.
    """
    original = "日本語の指示"
    data = original.encode("cp932")
    root = make_repo({"AGENTS.md": data})
    plan = build_load_plan(root, root, Config(max_bytes=1000))
    chunk = plan.chunks[0]

    # The budget counts bytes, and the byte count is exact regardless of encoding.
    assert chunk.file.raw_size == len(data)
    assert not chunk.truncated and not chunk.dropped

    # The text is mojibake: undecodable bytes become U+FFFD, while the ASCII-range
    # trailing bytes of CP932 pairs survive as stray letters. Character counts are
    # therefore meaningless here, which is exactly why byte accounting is the
    # source of truth.
    assert "\ufffd" in chunk.file.text
    assert chunk.file.char_count != len(original)


def test_non_utf8_file_is_not_mistaken_for_blank(make_repo):
    root = make_repo({"AGENTS.md": "日本語".encode("cp932")})
    plan = build_load_plan(root, root, Config(max_bytes=1000))
    assert not plan.chunks[0].blank
