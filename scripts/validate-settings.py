#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _require(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{label}: missing `{needle}`")


def _safe_read(path: Path, label: str, failures: list[str]) -> str:
    """파일이 없거나 읽기 실패 시 failures 로그에 기록하고 빈 문자열 반환.

    supervisor 배치가 Python traceback으로 hard-stop 하지 않도록 방어.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"{label}: missing file ({path})")
        return ""
    except OSError as exc:
        failures.append(f"{label}: read error ({exc})")
        return ""


def _soft_read(path: Path) -> str:
    """선택 파일 읽기. 없거나 실패하면 빈 문자열 (failures에 기록하지 않음)."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""


def _slice_section(text: str, key: str) -> str | None:
    """key를 포함하는 heading부터 동급 이상(<=) 레벨 heading 직전까지의 본문을 반환.

    §0 Voice Profile(## 레벨, 하위 ### 포함)과 §8.1 매트릭스(### 레벨) 모두 지원.
    heading을 못 찾으면 None.
    """
    lines = text.splitlines()
    start: int | None = None
    start_level = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#") and key in line:
            start = i
            start_level = len(stripped) - len(stripped.lstrip("#"))
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start + 1:]:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if level <= start_level:
                break
        body.append(line)
    return "\n".join(body)


def _matrix_data_rows(section: str) -> int:
    """§8.1 매트릭스 섹션에서 실기재된 데이터 행 수 (헤더/구분선/placeholder 제외)."""
    rows = 0
    for line in section.splitlines():
        cell = line.strip()
        if not cell.startswith("|"):
            continue
        if set(cell) <= set("|-: "):  # 구분선 |---|
            continue
        if "화자" in cell or "청자" in cell:  # 컬럼 헤더 행
            continue
        if "{{" in cell:  # placeholder 행은 실기재 아님
            continue
        rows += 1
    return rows


def _check_speech_matrix(claude_md: str, warnings: list[str]) -> None:
    """CLAUDE.md §8.1 호칭/어투 매트릭스 실기재 검사 (audit F4/F7, 항목 24).

    §8.1 부재 시 조용히 skip (비표준 프로젝트 오탐 방지).
    """
    section = _slice_section(claude_md, "호칭/어투 매트릭스")
    if section is None:
        return
    if "{{" in section:
        warnings.append(
            "CLAUDE.md §8.1 호칭/어투 매트릭스: placeholder({{...}}) 잔존 — "
            "매트릭스 미기재 (연재 후 FAIL 대상)"
        )
    elif _matrix_data_rows(section) == 0:
        warnings.append(
            "CLAUDE.md §8.1 호칭/어투 매트릭스: 데이터 행 0개 — "
            "매트릭스 미작성 (연재 후 FAIL 대상)"
        )


def _check_voice_profile_placeholder(style_guide: str, warnings: list[str]) -> None:
    """settings/01-style-guide.md §0 Voice Profile placeholder 검사 (audit F3, 항목 24).

    §0에 `{{`가 남으면 compile_brief가 Voice Profile 전체를 silent 탈락시킨다.
    """
    section = _slice_section(style_guide, "0. Voice Profile")
    if section is None:
        return
    if "{{" in section:
        warnings.append(
            "settings/01-style-guide.md §0 Voice Profile: placeholder({{...}}) 잔존 — "
            "compile_brief가 §0 전체를 silent 탈락시킬 수 있음"
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    failures: list[str] = []
    warnings: list[str] = []

    style_guide = _safe_read(
        novel_dir / "settings" / "01-style-guide.md",
        "01-style-guide.md",
        failures,
    )
    characters = _safe_read(
        novel_dir / "settings" / "03-characters.md",
        "03-characters.md",
        failures,
    )
    running_context = _safe_read(
        novel_dir / "summaries" / "running-context.md",
        "summaries/running-context.md",
        failures,
    )
    desire_state_path = novel_dir / "summaries" / "desire-state.md"
    signature_moves_path = novel_dir / "summaries" / "signature-moves.md"

    # Phase 6 fix (2026-04-17): 파일이 누락된 경우 같은 파일에 대한
    # 후속 _require 호출이 모두 "missing needle" 중복 FAIL을 내는 것을 방지.
    # _safe_read가 빈 문자열을 반환하면 needle 검사 skip.
    if style_guide:
        for needle in (
            "## 0. Voice Profile",
            "### 0.2 보이스 우선순위",
            "### 0.3 대표 문단",
            "## 1. 시점",
        ):
            _require(style_guide, needle, "01-style-guide.md", failures)

    if characters:
        for needle in (
            "## 캐릭터 시트 형식",
            "- **말투**:",
            "- **말 길이 경향**:",
            "- **금기/트리거**:",
            "- **회피 반응**:",
            "- **대표 대사 2~3종**:",
        ):
            _require(characters, needle, "03-characters.md", failures)

    if running_context:
        for needle in (
            "## Immediate Carry-Forward",
            "## 엔딩 훅 추적",
            "## HOLD 경고",
        ):
            _require(running_context, needle, "summaries/running-context.md", failures)

    if not desire_state_path.exists():
        failures.append("summaries/desire-state.md: missing file")
    else:
        desire_state = desire_state_path.read_text(encoding="utf-8")
        for needle in (
            "## Current Desire",
            "## Current Anxiety",
            "## This Episode Touchpoints",
        ):
            _require(desire_state, needle, "summaries/desire-state.md", failures)

    if not signature_moves_path.exists():
        failures.append("summaries/signature-moves.md: missing file")
    else:
        signature_moves = signature_moves_path.read_text(encoding="utf-8")
        for needle in (
            "## Opening Moves",
            "## Pressure Moves",
            "## Landing Moves",
            "## Overused Moves",
        ):
            _require(signature_moves, needle, "summaries/signature-moves.md", failures)

    # WARN 검사 (비치명적, exit code에 영향 없음 — 연재 후 FAIL 승격 대상).
    # §0 Voice Profile placeholder → compile_brief silent 탈락 위험 (audit F3).
    if style_guide:
        _check_voice_profile_placeholder(style_guide, warnings)
    # CLAUDE.md §8.1 호칭/어투 매트릭스 미기재 (audit F4). CLAUDE.md는 선택 읽기.
    claude_md = _soft_read(novel_dir / "CLAUDE.md")
    if claude_md:
        _check_speech_matrix(claude_md, warnings)

    for item in warnings:
        print(f"WARN {item}")

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1

    print("VALID settings/running-context contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
