#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _require(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{label}: missing `{needle}`")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    style_guide = (novel_dir / "settings" / "01-style-guide.md").read_text(
        encoding="utf-8"
    )
    characters = (novel_dir / "settings" / "03-characters.md").read_text(
        encoding="utf-8"
    )
    running_context = (
        novel_dir / "summaries" / "running-context.md"
    ).read_text(encoding="utf-8")

    failures: list[str] = []

    for needle in (
        "## 0. Voice Profile",
        "### 0.2 보이스 우선순위",
        "### 0.3 대표 문단",
        "## 1. 시점",
    ):
        _require(style_guide, needle, "01-style-guide.md", failures)

    for needle in (
        "## 캐릭터 시트 형식",
        "- **말투**:",
        "- **말 길이 경향**:",
        "- **금기/트리거**:",
        "- **회피 반응**:",
        "- **대표 대사 2~3종**:",
    ):
        _require(characters, needle, "03-characters.md", failures)

    for needle in (
        "## Immediate Carry-Forward",
        "## 엔딩 훅 추적",
    ):
        _require(running_context, needle, "summaries/running-context.md", failures)

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1

    print("VALID settings/running-context contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
