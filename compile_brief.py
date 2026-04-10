#!/usr/bin/env python3
"""
compile_brief — 소설 집필용 압축 브리프 생성기

여러 소설 프로젝트 파일(~300KB+)을 읽어서 해당 에피소드 집필에 필요한
핵심 정보만 추출한 단일 마크다운 문서(~4-6KB)를 생성한다.

사용 방식:
  1. MCP 도구로 호출 (compile_brief 함수)
  2. 직접 import하여 사용 (_compile_brief 내부 함수)
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ─── File I/O ──────────────────────────────────────────────


def _safe_read(path: str | Path) -> str:
    """파일을 읽되, 없거나 권한이 없으면 빈 문자열을 반환한다."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError):
        return ""


def _utc_now() -> str:
    """런타임 로그용 UTC 타임스탬프를 반환한다."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _append_runtime_line(path: Path, line: str) -> None:
    """런타임 로그 라인을 append한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip("\n") + "\n")


def _append_runtime_event(
    novel_dir: str | Path,
    event: str,
    **payload: Any,
) -> None:
    """tmp/run-metadata/events.jsonl에 이벤트를 기록한다."""
    event_path = Path(novel_dir) / "tmp" / "run-metadata" / "events.jsonl"
    record = {"ts": _utc_now(), "event": event, **payload}
    _append_runtime_line(
        event_path,
        json.dumps(record, ensure_ascii=False, sort_keys=True),
    )


def _relative_to_novel(
    novel_dir: str | Path,
    path: str | Path,
) -> str:
    """프로젝트 루트 기준 상대경로를 반환한다."""
    novel_path = Path(novel_dir).resolve()
    target = Path(path).resolve()
    try:
        return str(target.relative_to(novel_path))
    except ValueError:
        return str(path)


def _safe_read_logged(
    novel_dir: str | Path,
    path: str | Path,
    label: str,
    *,
    required: bool = False,
) -> str:
    """프로젝트 파일을 읽고 실패를 런타임 로그에 남긴다."""
    target = Path(path)
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError:
        if required:
            rel_path = _relative_to_novel(novel_dir, target)
            _append_runtime_line(
                Path(novel_dir) / "tmp" / "run-metadata" / "read-errors.log",
                f"{_utc_now()} missing label={label} path={rel_path}",
            )
            _append_runtime_event(
                novel_dir,
                "read_missing",
                label=label,
                path=rel_path,
            )
        return ""
    except (PermissionError, UnicodeDecodeError, OSError) as exc:
        rel_path = _relative_to_novel(novel_dir, target)
        _append_runtime_line(
            Path(novel_dir) / "tmp" / "run-metadata" / "read-errors.log",
            f"{_utc_now()} error label={label} path={rel_path} detail={type(exc).__name__}: {exc}",
        )
        _append_runtime_event(
            novel_dir,
            "read_error",
            label=label,
            path=rel_path,
            error_type=type(exc).__name__,
            detail=str(exc),
        )
        return ""


def _write_brief_snapshot(
    novel_dir: str | Path,
    episode_number: int,
    brief: str,
) -> Path:
    """compile_brief 결과 스냅샷을 tmp/briefs에 저장한다."""
    snapshot = (
        Path(novel_dir) / "tmp" / "briefs" / f"chapter-{episode_number:02d}.md"
    )
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(brief, encoding="utf-8")
    _append_runtime_event(
        novel_dir,
        "brief_snapshot_written",
        episode=episode_number,
        path=_relative_to_novel(novel_dir, snapshot),
        size_bytes=len(brief.encode("utf-8")),
    )
    return snapshot


def _clean_character_name(name: str) -> str:
    """캐릭터명에서 설명용 괄호를 제거해 표기 앵커를 만든다."""
    return re.sub(r"\s*\([^)]*\)", "", name).strip()


def _iter_plot_files(novel_dir: str) -> list[Path]:
    """집필 브리프에 사용할 plot 파일들을 순회한다."""
    plot_dir = Path(novel_dir) / "plot"
    if not plot_dir.exists():
        return []

    files: list[Path] = []
    for path in plot_dir.glob("*.md"):
        if path.name in {"master-outline.md", "foreshadowing.md", "timeline.md"}:
            continue
        if re.match(
            r"^(?:prologue|epilogue|arc-\d+|interlude(?:-\d+)?)\.md$",
            path.name,
        ):
            files.append(path)

    def _sort_key(path: Path) -> tuple[int, int | str]:
        stem = path.stem
        if stem == "prologue":
            return (0, 0)
        if stem.startswith("arc-"):
            try:
                return (1, int(stem.split("-", 1)[1]))
            except ValueError:
                return (1, stem)
        if stem.startswith("interlude"):
            match = re.search(r"(\d+)$", stem)
            return (2, int(match.group(1)) if match else 0)
        if stem == "epilogue":
            return (3, 0)
        return (4, stem)

    return sorted(files, key=_sort_key)


def _extract_episode_plot_block(content: str, episode_number: int) -> str:
    """플롯 파일에서 해당 화의 블록을 추출한다.

    지원 형식:
    - `## 5화: ...` / `### 67화: ...` 같은 화별 상세 섹션
    - `| 6 | 목표 | 훅 타입 | 핵심 장면 |` 같은 개별 에피소드 테이블
    """
    if not content:
        return ""

    for level in (2, 3, 4):
        pattern = re.compile(
            rf"(?ms)^#{{{level}}}\s*{episode_number}화[^\n]*\n"
            rf".*?(?=^#{{1,{level}}}\s+|\Z)"
        )
        match = pattern.search(content)
        if match:
            return match.group(0).strip()

    lines = content.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        if int(cells[0]) != episode_number:
            continue

        block_title = ""
        for back in range(idx - 1, -1, -1):
            header = lines[back].strip()
            if header.startswith("### "):
                block_title = header[4:].strip()
                break

        parts: list[str] = []
        if block_title:
            parts.append(f"### {block_title}")
        parts.append(f"## {episode_number}화")
        parts.append(f"- 목표: {cells[1]}")
        if len(cells) > 2 and cells[2]:
            parts.append(f"- 훅 타입: {cells[2]}")
        if len(cells) > 3 and cells[3]:
            parts.append(f"- 핵심 장면: {cells[3]}")
        return "\n".join(parts)

    return ""


def _find_episode_chapter_path(
    novel_dir: str, episode_number: int
) -> Optional[Path]:
    """episode_number에 해당하는 chapter 파일 경로를 찾는다."""
    chapters_dir = Path(novel_dir) / "chapters"
    if not chapters_dir.exists():
        return None

    for path in sorted(chapters_dir.glob("**/chapter-*.md")):
        match = re.search(r"chapter-(\d+)\.md$", path.name)
        if match and int(match.group(1)) == episode_number:
            return path
    return None


def _extract_characters_from_episode_meta(content: str) -> list[str]:
    """EPISODE_META의 characters_appeared를 추출한다."""
    if not content:
        return []

    meta_match = re.search(
        r"### EPISODE_META\s*```yaml(.*?)```",
        content,
        re.DOTALL,
    )
    if not meta_match:
        return []

    characters: list[str] = []
    in_characters = False
    for line in meta_match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("characters_appeared:"):
            in_characters = True
            continue
        if not in_characters:
            continue
        if stripped.startswith("- "):
            characters.append(_clean_character_name(stripped[2:].strip()))
            continue
        if re.match(r"[a-z_]+:", stripped):
            break
        if stripped:
            break

    return [c for c in characters if c]


def _strip_episode_meta(content: str) -> str:
    """본문에서 EPISODE_META 이하를 제거한다."""
    return re.sub(
        r"\n---\s*\n### EPISODE_META\s*```yaml.*",
        "",
        content,
        flags=re.DOTALL,
    ).strip()


def _extract_previous_episode_anchor(
    novel_dir: str, episode_number: int
) -> str:
    """직전 화 마지막 장면을 오프닝 앵커용으로 압축 추출한다."""
    prev_ep = episode_number - 1
    if prev_ep <= 0:
        return ""

    prev_path = _find_episode_chapter_path(novel_dir, prev_ep)
    if not prev_path:
        return ""

    prev_content = _safe_read(prev_path)
    if not prev_content:
        return ""

    body = _strip_episode_meta(prev_content)
    body = re.sub(r"^#.*\n+", "", body).strip()
    if not body:
        return ""

    scenes = [
        scene.strip()
        for scene in re.split(r"(?m)^\*\*\*\s*$", body)
        if scene.strip()
    ]
    last_scene = scenes[-1] if scenes else body
    paragraphs = [p.strip() for p in last_scene.split("\n\n") if p.strip()]
    excerpt = "\n\n".join(
        paragraphs[-8:] if len(paragraphs) > 8 else paragraphs
    )

    if len(excerpt) > 1800:
        excerpt = excerpt[:1800].rstrip() + "\n...(생략)"

    rules = [
        "- 아래 장면에서 실제로 끝난 일만 다음 화 오프닝의 기정사실로 이어간다.",
        "- 보고/허락/안심/소문 확산/관아 전달/관계 변화는 본문에 보이지 않았으면 아직 발생하지 않은 것으로 본다.",
    ]
    return "\n".join(rules) + "\n\n### 직전 화 마지막 장면\n\n" + excerpt


def _extract_ending_hook_tracking(running_context: str) -> str:
    """running-context의 엔딩 훅 추적 테이블을 압축 추출한다."""
    if not running_context:
        return ""

    match = re.search(
        r"## (?:엔딩 훅 추적(?:\s*\(최근 \d+화\))?|Ending Hook Tracking)\s*\n(.*?)(?=\n## |$)",
        running_context,
        re.DOTALL,
    )
    if not match:
        return ""

    rows: list[str] = []
    for line in match.group(1).strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "{{" in stripped:
            continue
        rows.append(stripped)

    if len(rows) < 3:
        return ""

    if len(rows) <= 7:
        return "\n".join(rows)
    return "\n".join(rows[:2] + rows[-5:])


def _extract_live_cue_lines(
    text: str,
    *,
    heading_pattern: str,
    limit: int,
) -> list[str]:
    """지정된 헤더 아래 bullet/table line을 cue용으로 뽑는다."""
    if not text:
        return []

    match = re.search(heading_pattern, text, re.DOTALL)
    if not match:
        return []

    lines: list[str] = []
    for raw in match.group(1).strip().splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ", "|", ">")):
            lines.append(stripped)
    return lines[:limit]


def _extract_voice_priority(style_guide: str) -> list[str]:
    """Voice Profile 우선순위 3개를 추출한다."""
    if not style_guide:
        return []

    match = re.search(
        r"### 0\.2 보이스 우선순위\s*\n(.*?)(?=\n### 0\.3|\n## 1\.|$)",
        style_guide,
        re.DOTALL,
    )
    if not match:
        return []

    priorities: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if re.match(r"\d+\.", stripped):
            priorities.append(re.sub(r"^\d+\.\s*", "", stripped))
    return priorities[:3]


def _extract_lexicon_rows(style_lexicon: str, limit: int = 4) -> list[str]:
    """style-lexicon의 데이터 행을 추출한다."""
    rows: list[str] = []
    for line in style_lexicon.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "→" in stripped:
            rows.append(stripped)
    return rows[:limit]


def _extract_recent_repetition_rows(
    watchlist: str, limit: int = 4
) -> list[str]:
    """WATCH/HIGH watchlist 행만 추출한다."""
    rows: list[str] = []
    for line in watchlist.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("| ID"):
            continue
        if "WATCH" in stripped or "HIGH" in stripped:
            rows.append(stripped)
    return rows[:limit]


def _extract_recent_decisions(
    decision_log: str, limit: int = 3
) -> list[str]:
    """decision-log 데이터 행을 cue용으로 추출한다."""
    rows: list[str] = []
    for line in decision_log.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "규칙" in stripped:
            continue
        if set(stripped) <= {"|", "-", " "}:
            continue
        rows.append(stripped)
    return rows[:limit]


def _build_live_drafting_cues(
    *,
    goals: str,
    prev_anchor: str,
    running_context: str,
    style_guide: str,
    style_lexicon: str,
    dialogue_log: str,
    relationship_log: str,
    watchlist: str,
    decision_log: str,
) -> str:
    """집필 시작 전 빠르게 읽을 cue 묶음을 만든다."""
    blocks: list[str] = []

    goal_lines = [
        line.strip()
        for line in goals.splitlines()
        if line.strip().startswith(
            ("- 목표:", "- 훅 타입:", "- 핵심 장면:")
        )
    ][:3]
    if not goal_lines:
        goal_lines = [
            line.strip()
            for line in goals.splitlines()
            if line.strip().startswith("- ")
        ][:3]
    if goal_lines:
        blocks.append("### 이번 화 기능\n\n" + "\n".join(goal_lines))

    if prev_anchor:
        excerpt = prev_anchor.split("### 직전 화 마지막 장면", 1)[-1].strip()
        if excerpt:
            paragraphs = [p.strip() for p in excerpt.split("\n\n") if p.strip()]
            anchor_excerpt = "\n\n".join(paragraphs[:2])
            blocks.append("### 직전 화 마지막 장면 압축\n\n" + anchor_excerpt)

    immediate_lines = _extract_live_cue_lines(
        running_context,
        heading_pattern=r"## (?:직전 화 직결 상태|Immediate Carry-Forward|Carry-Forward)\s*\n(.*?)(?=\n## |$)",
        limit=5,
    )
    if immediate_lines:
        blocks.append("### 오프닝에서 놓치면 안 되는 상태\n\n" + "\n".join(immediate_lines))

    hook_table = _extract_ending_hook_tracking(running_context)
    if hook_table:
        blocks.append("### 최근 엔딩 훅 추적\n\n" + hook_table)

    priorities = _extract_voice_priority(style_guide)
    if priorities:
        blocks.append(
            "### 이번 화 보이스 우선순위\n\n"
            + "\n".join(f"- {line}" for line in priorities)
        )

    lexicon_rows = _extract_lexicon_rows(style_lexicon)
    if lexicon_rows:
        blocks.append(
            "### 최근 채택 어휘 치환\n\n"
            + "| 패턴 | 치환 |\n|------|------|\n"
            + "\n".join(lexicon_rows)
        )

    dialogue_rows = [
        line.strip()
        for line in dialogue_log.splitlines()
        if line.strip().startswith("|") and not line.strip().startswith("|----")
    ][:4]
    if len(dialogue_rows) > 1:
        blocks.append("### 대사 운용 경고\n\n" + "\n".join(dialogue_rows))

    turning_points = _extract_relationship_turning_points(relationship_log)
    if turning_points:
        blocks.append(turning_points)

    recent_repetition = _extract_recent_repetition_rows(watchlist)
    if recent_repetition:
        blocks.append(
            "### 반복 패턴 주의\n\n"
            + "| ID | 유형 | 패턴 | 현재 빈도 | 허용 한도 | 비고 |\n"
            + "|----|----|------|---------|---------|------|\n"
            + "\n".join(recent_repetition)
        )

    recent_decisions = _extract_recent_decisions(decision_log)
    if recent_decisions:
        blocks.append(
            "### 유지 중인 규칙 이탈\n\n"
            + "| 규칙 | 적용 범위 | 이유 | 종료 조건 |\n"
            + "|------|----------|------|-----------|\n"
            + "\n".join(recent_decisions)
        )

    return "\n\n".join(blocks)


# ─── Parsers ───────────────────────────────────────────────


def _extract_characters_from_plot(
    novel_dir: str, episode_number: int
) -> list[str]:
    """plot 파일에서 해당 에피소드의 등장인물 목록을 추출한다.

    화별 상세 섹션 또는 개별 에피소드 테이블 행을 찾고, 다음 순서로 추출한다.
    1. `등장인물`/`characters` 명시 줄
    2. plot 블록 안에 실제로 언급된 tracked character 이름
    3. 직전 화 EPISODE_META / episode-log 폴백
    """
    characters: list[str] = []

    plot_dir = Path(novel_dir) / "plot"
    if not plot_dir.exists():
        return characters

    tracked_names = _extract_all_tracked_characters(
        Path(novel_dir) / "summaries" / "character-tracker.md"
    )

    for plot_file in _iter_plot_files(novel_dir):
        block = _extract_episode_plot_block(_safe_read(plot_file), episode_number)
        if not block:
            continue

        # 등장인물 줄 파싱
        for line in block.splitlines():
            if "등장인물" in line or "characters" in line.lower():
                after_colon = line.split(":", 1)[-1] if ":" in line else line
                cleaned = re.sub(r"\([^)]*\)", "", after_colon)
                names = [
                    _clean_character_name(n.strip().strip("*"))
                    for n in cleaned.split(",")
                    if n.strip()
                ]
                characters.extend(names)
                break

        if characters:
            break

        matched = [
            name for name in tracked_names
            if name and name not in characters and name in block
        ]
        if matched:
            characters.extend(matched[:6])
            break

        # 표 행 기반 플롯은 인물명이 생략되는 경우가 많다.
        # 이때는 직전 화 메타를 넓게 끌어오기보다 주인공 앵커 1명을 우선 둔다.
        if block and tracked_names:
            characters.append(tracked_names[0])
            break

    if not characters:
        characters = _extract_characters_from_episode_log(
            novel_dir, episode_number
        )

    seen: set[str] = set()
    deduped: list[str] = []
    for name in characters:
        clean = _clean_character_name(name)
        if clean and clean not in seen:
            seen.add(clean)
            deduped.append(clean)

    return deduped


def _extract_characters_from_episode_log(
    novel_dir: str, episode_number: int
) -> list[str]:
    """직전 화의 EPISODE_META 또는 episode-log에서 등장인물을 추출한다."""
    prev_ep = episode_number - 1
    if prev_ep <= 0:
        return []

    prev_path = _find_episode_chapter_path(novel_dir, prev_ep)
    if prev_path:
        meta_chars = _extract_characters_from_episode_meta(_safe_read(prev_path))
        if meta_chars:
            return meta_chars

    content = _safe_read(Path(novel_dir) / "summaries" / "episode-log.md")
    if not content:
        return []

    tracker_names = _extract_all_tracked_characters(
        Path(novel_dir) / "summaries" / "character-tracker.md"
    )
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        if int(cells[0]) != prev_ep:
            continue

        haystack = " ".join(cells[1:3])
        matched = [name for name in tracker_names if name and name in haystack]
        return matched[:6]

    return []


def _filter_character_tracker(
    content: str, characters: list[str]
) -> str:
    """character-tracker.md에서 지정된 캐릭터 섹션만 추출한다.

    형식:
      ### 캐릭터이름
      - **항목**: 값
      ...
      ---
    """
    if not content or not characters:
        return content if content else "(파일 없음)"

    blocks: list[str] = []
    # ### 헤더로 분리
    sections = re.split(r"(?=^### )", content, flags=re.MULTILINE)

    for section in sections:
        header_match = re.match(r"### (.+)", section)
        if not header_match:
            continue
        name = header_match.group(1).strip()
        # 캐릭터 이름이 섹션 헤더에 포함되는지 확인
        # "인격체 서하 (NPD-CONV-YSH-001)" 같은 경우도 매칭
        if any(char in name for char in characters):
            # --- 구분선 이전까지만, 핵심 항목만 추출
            block_lines: list[str] = []
            for bline in section.strip().rstrip("-").strip().splitlines():
                stripped = bline.strip()
                # 헤더는 항상 포함
                if stripped.startswith("###"):
                    block_lines.append(stripped)
                # 핵심 항목만 포함 (현재 위치, 상태, 핵심 동기, 미해결)
                elif any(
                    k in stripped
                    for k in [
                        "현재 위치", "위치", "상태", "정신 상태",
                        "경지", "부상", "핵심 동기", "미해결",
                        "Current Location", "Current Status", "Status",
                        "Injury", "Injuries", "Notes", "비고",
                        "Knowledge", "Current Goal",
                    ]
                ):
                    # 200자 제한
                    if len(stripped) > 200:
                        block_lines.append(stripped[:200] + "...")
                    else:
                        block_lines.append(stripped)
            blocks.append("\n".join(block_lines))

    return "\n\n".join(blocks) if blocks else "(해당 캐릭터 없음)"


def _filter_knowledge_map(
    content: str, characters: list[str]
) -> str:
    """knowledge-map.md에서 지정된 캐릭터의 열만 추출한다.

    원본 형식:
      | 정보 | 윤서하 | 리라 | 비고 |
      |------|--------|------|------|
      | 강하윤 사망 사실 | O(1화) | O(1화) | 설명 |

    캐릭터 컬럼 인덱스를 찾아 해당 열만 남긴다.
    1000줄 이상이므로 최근 에피소드(episode_number 기준)와 관련 있는 행만 남긴다.
    """
    if not content or not characters:
        return "(파일 없음)"

    if "(초기화)" in content:
        return "(정보 보유 기록 없음)"

    lines = content.splitlines()

    # 테이블 헤더 행을 찾는다 (| 정보 | 캐릭터1 | ... |)
    header_line_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|") and "정보" in line:
            header_line_idx = i
            break

    if header_line_idx is None:
        return "(정보 보유 기록 없음)"

    header = lines[header_line_idx]
    cols = [c.strip() for c in header.split("|")]
    # cols[0]과 cols[-1]은 빈 문자열 (| 앞뒤)

    # 항상 포함할 열: 정보(첫째), 비고(마지막)
    # 캐릭터에 해당하는 열 인덱스를 수집
    keep_indices: list[int] = []
    for idx, col in enumerate(cols):
        if not col:
            continue
        if col == "정보" or col == "비고":
            keep_indices.append(idx)
        elif any(char in col for char in characters):
            keep_indices.append(idx)

    if len(keep_indices) <= 2:
        # 정보+비고만 있으면 캐릭터 열을 못 찾은 것
        return "(해당 캐릭터 열 없음)"

    keep_indices.sort()

    # 헤더 + 구분선 + 데이터 행 필터링
    result_lines: list[str] = []

    for i in range(header_line_idx, len(lines)):
        line = lines[i]
        if not line.startswith("|"):
            continue

        row_cols = line.split("|")
        # 필터링된 열만 남기기
        filtered = [
            row_cols[j] if j < len(row_cols) else ""
            for j in keep_indices
        ]
        result_lines.append("|" + "|".join(filtered) + "|")

    # 결과가 너무 길면 최근 정보만 (마지막 25행)
    # 장편(60화+)에서 15행은 핵심 지식을 놓칠 수 있으므로 25행으로 확대.
    # 전역 핵심 정보(비밀/오해 등)는 _extract_global_knowledge로 별도 보장됨.
    max_data_rows = 25
    if len(result_lines) > max_data_rows + 2:  # 헤더+구분선+N행
        header_rows = result_lines[:2]
        data_rows = result_lines[2:]
        result_lines = (
            header_rows
            + [f"| ... ({len(data_rows) - max_data_rows}행 생략) |" + "|" * (len(keep_indices) - 1)]
            + data_rows[-max_data_rows:]
        )

    return "\n".join(result_lines)


def _filter_relationship_log(
    content: str, characters: list[str]
) -> str:
    """relationship-log.md에서 지정된 캐릭터가 관여된 쌍만 추출한다.

    두 가지 섹션을 처리한다:
    1. 관계 매트릭스 테이블 — 캐릭터 행/열만 추출
    2. 만남 로그 테이블 — 캐릭터 이름이 포함된 행만 추출
    """
    if not content or not characters:
        return "(파일 없음)"

    parts: list[str] = []

    # 1. 관계 매트릭스
    matrix_match = re.search(
        r"## (?:관계 매트릭스|관계 상태 매트릭스)\s*\n((?:\|.+\n)+)", content
    )
    if matrix_match:
        matrix_text = matrix_match.group(1)
        matrix_lines = matrix_text.strip().splitlines()
        if len(matrix_lines) >= 2:
            header_cells = [
                c.strip().strip("*")
                for c in matrix_lines[0].split("|")[1:-1]
            ]

            # 보이는 표 셀 기준으로 유지할 열 인덱스를 계산한다.
            # 첫 열은 항상 행 이름(A \ B / 캐릭터명)이므로 유지한다.
            keep_cols: list[int] = [0]
            for idx, col in enumerate(header_cells[1:], start=1):
                compact = col.replace(" ", "")
                if compact in {"A\\B", "A/B"} or "→" in col:
                    keep_cols.append(idx)
                elif any(char in col for char in characters):
                    keep_cols.append(idx)

            keep_cols = sorted(set(keep_cols))

            # 캐릭터가 포함된 행만 추출
            filtered_rows: list[str] = []
            for row_idx, line in enumerate(matrix_lines):
                row_cols = [c.strip() for c in line.split("|")[1:-1]]
                if not row_cols:
                    continue

                # 행의 첫 번째 데이터 열에 캐릭터 이름이 있는지
                first_data = row_cols[0].strip().strip("*")
                compact_first = first_data.replace(" ", "")
                is_header = row_idx == 0 or "A\\B" in compact_first or "A/B" in compact_first
                is_separator = row_idx == 1 or all(
                    set(cell) <= {"-", ":"} for cell in row_cols if cell
                )
                is_char_row = any(char in first_data for char in characters)

                if is_header or is_separator or is_char_row:
                    filtered = [
                        row_cols[j] if j < len(row_cols) else ""
                        for j in keep_cols
                    ]
                    filtered_rows.append("| " + " | ".join(filtered) + " |")

            # 셀 내용을 80자로 제한
            truncated_rows: list[str] = []
            for row in filtered_rows:
                cols = [c.strip() for c in row.split("|")[1:-1]]
                cols = [
                    c[:60] + "..." if len(c) > 60 else c
                    for c in cols
                ]
                truncated_rows.append("| " + " | ".join(cols) + " |")

            if truncated_rows:
                parts.append("### 관계 매트릭스\n\n" + "\n".join(truncated_rows))

    # 2. 만남 로그 — 최근 항목 중 캐릭터가 포함된 것만
    log_match = re.search(r"## 만남 로그\s*\n((?:\|.+\n)+)", content)
    if log_match:
        log_text = log_match.group(1)
        log_lines = log_text.strip().splitlines()
        if len(log_lines) >= 2:
            header = log_lines[0]
            separator = log_lines[1]
            filtered = [header, separator]
            for line in log_lines[2:]:
                if any(char in line for char in characters):
                    filtered.append(line)

            # 최근 5건만, 셀 내용 150자 제한
            if len(filtered) > 7:
                filtered = filtered[:2] + filtered[-5:]

            # 각 데이터 행의 셀을 150자로 제한
            truncated = []
            for line in filtered:
                if line.startswith("|") and not all(c in "-| " for c in line):
                    cols = line.split("|")
                    cols = [
                        c[:80] + "..." if len(c.strip()) > 80 else c
                        for c in cols
                    ]
                    truncated.append("|".join(cols))
                else:
                    truncated.append(line)

            parts.append("### 최근 만남 로그\n\n" + "\n".join(truncated))

    return "\n\n".join(parts) if parts else "(해당 캐릭터 관계 없음)"


def _filter_promise_tracker(content: str) -> str:
    """promise-tracker.md에서 활성 약속(미해결/진행중)만 추출한다.

    '## 활성 약속' 섹션의 테이블에서 status가 완료가 아닌 항목을 가져온다.
    완료/무효화 섹션은 건너뛴다.
    """
    if not content:
        return "(파일 없음)"

    # '## 활성 약속' 또는 '## 활성 약속 (미이행)' 섹션 추출
    active_match = re.search(
        r"## 활성 약속(?:\s*\(미이행\))?\s*\n(.*?)(?=\n## |$)",
        content,
        re.DOTALL,
    )
    if not active_match:
        return "(활성 약속 없음)"

    section = active_match.group(1).strip()

    # 테이블을 간결한 리스트 형식으로 변환 (테이블은 너무 넓어서 읽기 어렵다)
    lines = section.splitlines()
    result: list[str] = []

    for line in lines:
        if not line.startswith("|"):
            continue
        # 구분선 건너뛰기
        if all(c in "-| " for c in line):
            continue
        # 헤더행 건너뛰기
        if "ID" in line and "당사자" in line:
            continue

        cols = [c.strip() for c in line.split("|")]
        # cols: ['', ID, 당사자, 내용, 투하, 예정회수, 우선순위, 상세, '']
        cols = [c for c in cols if c]  # 빈 문자열 제거
        if len(cols) < 4:
            continue

        pid = cols[0]
        parties = cols[1]
        desc = cols[2]
        # 상세에서 최근 진전만 (마지막 100자)
        detail = cols[-1] if len(cols) > 5 else ""
        status = cols[4] if len(cols) > 4 else ""
        priority = cols[5] if len(cols) > 5 else ""

        # 최근 진전 추출
        latest = ""
        if detail:
            progress = re.findall(
                r"\*\*(\d+화)[^*]*\*\*", detail
            )
            if progress:
                latest = f" (최근: {progress[-1]})"

        result.append(
            f"- **{pid}** {parties}: {desc[:80]}"
            f" [{status}]{latest}"
        )

    return "\n".join(result) if result else "(활성 약속 없음)"


def _filter_foreshadowing(content: str) -> str:
    """foreshadowing.md에서 활성/투하예정 복선만 추출한다.

    '## 활성 복선 (미회수)' 섹션에서 각 복선의 ID, 설치, 내용, 현재 진전만 뽑는다.
    이미 회수 완료된 것은 한 줄 요약만 포함한다.
    """
    if not content:
        return "(파일 없음)"

    parts: list[str] = []

    # 활성 복선 섹션의 각 F### 항목에서 핵심만 추출
    active_match = re.search(
        r"## 활성 복선 \(미회수\)\s*\n(.*?)(?=\n## 회수 완료|$)",
        content,
        re.DOTALL,
    )
    if active_match:
        active_section = active_match.group(1)
        # 각 ### FXXX 블록을 파싱
        foreshadow_blocks = re.split(
            r"(?=^### F\d+)", active_section, flags=re.MULTILINE
        )
        for block in foreshadow_blocks:
            if not block.strip():
                continue
            # 제목
            title_match = re.match(r"### (F\d+)\. (.+)", block)
            if not title_match:
                continue
            fid = title_match.group(1)
            fname = title_match.group(2).strip()

            # 회수 완료인지 확인
            if "회수 완료" in block:
                # 회수 완료 복선은 한 줄만
                recovery_match = re.search(
                    r"- \*\*회수 완료\*\*: (\d+화)", block
                )
                ep = recovery_match.group(1) if recovery_match else "?"
                parts.append(f"- **{fid}. {fname}** — 회수 완료 ({ep})")
                continue

            # 설치/내용
            setup_match = re.search(r"- \*\*설치\*\*: (.+)", block)
            content_match = re.search(r"- \*\*내용\*\*: (.+)", block)

            setup = setup_match.group(1) if setup_match else "?"
            desc = content_match.group(1) if content_match else "?"

            # 가장 최근 진전만 추출
            progress_matches = re.findall(
                r"- \*\*(\d+화[^*]*)\*\*: (.+?)(?=\n- \*\*\d+화|\n- \*\*회수|$)",
                block,
                re.DOTALL,
            )
            latest = ""
            if progress_matches:
                ep_label, detail = progress_matches[-1]
                # 첫 줄만
                first_line = detail.strip().splitlines()[0]
                latest = f" | 최근: **{ep_label}** — {first_line[:150]}"

            parts.append(
                f"- **{fid}. {fname}** (설치: {setup}) — {desc[:100]}{latest}"
            )

    # 회수 완료 테이블은 한 줄 요약으로
    completed_match = re.search(
        r"## 회수 완료\s*\n((?:\|.+\n)+)", content
    )
    if completed_match:
        table = completed_match.group(1).strip()
        table_lines = table.splitlines()
        if len(table_lines) > 2:
            parts.append("\n**회수 완료**: " + ", ".join(
                re.findall(r"F\d+", line)[-1]
                for line in table_lines[2:]
                if re.findall(r"F\d+", line)
            ))

    return "\n".join(parts) if parts else "(복선 없음)"


def _extract_last_n_episodes(
    content: str, n: int = 3, before_episode: int = 0
) -> str:
    """episode-log.md에서 마지막 N개 에피소드 요약을 추출한다.

    before_episode가 지정되면 그 에피소드 이전의 N개를 가져온다.
    """
    if not content:
        return "(파일 없음)"

    # 표 형식 episode-log 우선 지원
    table_rows: list[tuple[int, str, str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        ep_num = int(cells[0])
        if before_episode > 0 and ep_num >= before_episode:
            continue
        table_rows.append((ep_num, cells[1], cells[2]))

    if table_rows:
        table_rows.sort(key=lambda x: x[0])
        selected = table_rows[-n:]
        return "\n\n".join(
            f"### {ep_num}화 — {title}\n- 요약: {summary[:240]}"
            for ep_num, title, summary in selected
        )

    # --- 구분선으로 섹션 분리
    sections = re.split(r"\n---\n", content)
    episode_sections: list[tuple[int, str]] = []

    for section in sections:
        ep_match = re.match(r"\s*###?\s*(\d+)화", section.strip())
        if ep_match:
            ep_num = int(ep_match.group(1))
            if before_episode > 0 and ep_num >= before_episode:
                continue
            episode_sections.append((ep_num, section.strip()))

    if not episode_sections:
        return "(에피소드 없음)"

    # 번호순 정렬 후 마지막 N개
    episode_sections.sort(key=lambda x: x[0])
    selected = episode_sections[-n:]

    result: list[str] = []
    for ep_num, section in selected:
        # 각 에피소드에서 요약 + 등장인물 + 엔딩 훅만 추출
        lines = section.splitlines()
        compressed: list[str] = []

        for line in lines:
            stripped = line.strip()
            # 헤더
            if stripped.startswith("###") or stripped.startswith("##"):
                compressed.append(stripped)
            # 요약, 등장인물, 엔딩 훅만 포함
            elif any(
                k in stripped
                for k in ["요약", "등장인물", "엔딩 훅"]
            ):
                # 200자 제한
                if len(stripped) > 250:
                    compressed.append(stripped[:250] + "...")
                else:
                    compressed.append(stripped)

        result.append("\n".join(compressed))

    return "\n\n".join(result)


def _filter_dialogue_log(
    content: str, characters: list[str], before_episode: int
) -> str:
    """dialogue-log.md에서 등장인물의 최근 대화 운용을 추출한다.

    행 유형:
    - 이탈 행: 톤 델타/관계톤/지향이 채워진 행 (보이스 drift 정보)
    - role-only 행: 대화 기능만 기록, 나머지 "—" (역할 고착 판정용)

    추출 우선순위: 이탈 행 > role-only 행.
    캐릭터당 최대 2행, 전체 최대 8행, 섹션 하드캡 1200자.
    """
    if not content:
        return ""

    # 테이블 행 파싱 (헤더/구분선 제외)
    rows: list[dict] = []
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        # 헤더/구분선 스킵: 숫자가 없는 행은 모두 제외
        ep_str = re.sub(r"[^0-9]", "", cells[0])
        if not ep_str:
            continue
        ep_num = int(ep_str)
        if ep_num >= before_episode:
            continue
        # 이탈 행 vs role-only 행 판별 (톤 델타가 "—"이면 role-only)
        is_deviation = len(cells) > 3 and cells[3].strip() not in ("—", "-", "")
        rows.append({
            "episode": ep_num,
            "character": cells[1],
            "line": line,
            "is_deviation": is_deviation,
        })

    if not rows:
        return ""

    # 캐릭터 필터
    include_all = not characters
    matched_chars: list[str] = []
    seen_chars: set[str] = set()

    for row in rows:
        char = row["character"]
        if not include_all and not any(c in char for c in characters):
            continue
        if char not in seen_chars:
            seen_chars.add(char)
            matched_chars.append(char)

    # 각 캐릭터별: 이탈 행 우선, role-only 보조. 캐릭터당 최대 2행.
    result_lines: list[str] = []
    for char in matched_chars:
        char_rows = [r for r in rows if r["character"] == char]
        if not char_rows:
            continue

        recent_cutoff = before_episode - 3
        # 이탈 행: 최근 3화 내 + 마지막 이탈 1건
        dev_rows = [r for r in char_rows if r["is_deviation"]]
        recent_dev = [r for r in dev_rows if r["episode"] >= recent_cutoff]
        if dev_rows and dev_rows[-1] not in recent_dev:
            recent_dev.append(dev_rows[-1])

        # role-only 행: 최신 1건 (역할 고착 판정 보조)
        role_rows = [r for r in char_rows if not r["is_deviation"]]
        latest_role = [role_rows[-1]] if role_rows else []

        # 이탈 우선 합치기, 최대 2행
        combined = recent_dev + latest_role
        # 중복 제거 + 최신 우선
        seen_lines: set[str] = set()
        unique: list[dict] = []
        for r in sorted(combined, key=lambda x: x["episode"], reverse=True):
            if r["line"] not in seen_lines:
                seen_lines.add(r["line"])
                unique.append(r)
        for r in unique[:2]:
            result_lines.append(r["line"])

    if not result_lines:
        return ""

    # 전체 캡: 최대 8행
    result_lines = result_lines[:8]

    header = "| 화 | 캐릭터 | 대화 기능 | 톤 델타 | 관계톤 | 지향 |\n"
    header += "|----|--------|----------|---------|--------|------|\n"
    output = header + "\n".join(result_lines)

    # 섹션 하드캡: 1200자
    if len(output) > 1200:
        lines = output.splitlines()
        truncated = lines[:2]  # 헤더 + 구분선
        total = sum(len(l) for l in truncated) + len(truncated)
        for line in lines[2:]:
            if total + len(line) + 1 > 1200:
                break
            truncated.append(line)
            total += len(line) + 1
        output = "\n".join(truncated)

    return output


def _extract_character_slice(
    novel_dir: str, characters: list[str]
) -> str:
    """settings/03-characters.md에서 등장인물의 핵심 필드만 추출한다.

    추출 필드: 이름, 성격/말투, 동기, 금기/트리거, 대표 대사.
    전체 캐릭터 시트가 아니라 이번 화 집필에 필요한 최소 정보만.
    characters가 빈 리스트이면 모든 캐릭터 섹션을 추출한다.
    """
    novel_path = Path(novel_dir)
    content = _safe_read(novel_path / "settings" / "03-characters.md")
    if not content:
        return ""

    # 캐릭터별 섹션을 ##/### 헤더로 분리
    char_sections = re.split(r"(?=^#{2,3}\s)", content, flags=re.MULTILINE)

    # characters가 비어있으면 모든 캐릭터 섹션 포함
    include_all = not characters

    result: list[str] = []
    for section in char_sections:
        # 이 섹션이 등장인물과 관련있는지 확인
        if not include_all and not any(char in section[:200] for char in characters):
            continue

        # 핵심 필드만 추출
        lines = section.strip().splitlines()
        if not lines:
            continue

        header = lines[0]
        extracted: list[str] = [header]

        # 키워드 기반 필드 추출
        keep_keywords = [
            "성격", "말투", "동기", "목표", "금기", "트리거",
            "대표 대사", "특징", "호칭", "어투", "감정 표현",
            "행동 패턴", "습관", "외형", "말 길이", "회피 반응",
            "대화 대비축"  # 외형은 간략히 포함
        ]

        in_relevant = False
        for line in lines[1:]:
            # 하위 헤더나 볼드 키워드로 섹션 감지
            is_key_line = any(kw in line for kw in keep_keywords)
            is_sub_header = line.startswith("#") or line.startswith("**")
            is_list_item = line.startswith("- ") or line.startswith("  -")
            is_table = line.startswith("|")

            if is_key_line or (is_sub_header and any(kw in line for kw in keep_keywords)):
                in_relevant = True
                extracted.append(line)
            elif in_relevant and (is_list_item or is_table or line.startswith("  ")):
                extracted.append(line)
            elif in_relevant and line.strip() == "":
                extracted.append("")
            elif is_sub_header:
                # 새 섹션인데 관련 키워드 아님 → 관련 영역 종료
                in_relevant = False
            # 대표 대사 블록 (코드블록/인용)
            elif in_relevant and (line.startswith(">") or line.startswith("```")):
                extracted.append(line)

        if len(extracted) > 1:  # 헤더만 있으면 스킵
            result.append("\n".join(extracted))

    return "\n\n".join(result) if result else ""


def _extract_claude_md_rules(content: str) -> str:
    """CLAUDE.md에서 금지사항 + §5.1 의도적 미스터리 + 호칭/어투 매트릭스를 추출한다."""
    if not content:
        return "(파일 없음)"

    parts: list[str] = []

    # 금지사항 섹션 — 번호 항목만 추출 (설명 제거)
    # 한국어("금지 사항") 또는 영어("Prohibitions") 헤딩 모두 매칭
    prohib_match = re.search(
        r"## 5\.\s*(?:금지 사항|Prohibitions)\s*\n(.*?)(?=\n### 5\.1|$)",
        content,
        re.DOTALL,
    )
    if not prohib_match:
        # §5.1이 없는 경우 원래 패턴으로 폴백
        prohib_match = re.search(
            r"## 5\.\s*(?:금지 사항|Prohibitions)\s*\n(.*?)(?=\n## \d|$)",
            content,
            re.DOTALL,
        )
    if prohib_match:
        prohib_lines = []
        for line in prohib_match.group(1).strip().splitlines():
            stripped = line.strip()
            if re.match(r"\d+\.", stripped):
                # "1. **캐릭터 성격 급변 금지**: 설명..." -> 볼드 부분만
                bold_match = re.search(r"\*\*(.+?)\*\*", stripped)
                if bold_match:
                    prohib_lines.append(f"- {bold_match.group(1)}")
                else:
                    prohib_lines.append(f"- {stripped[:60]}")
        parts.append("### 금지사항\n\n" + "\n".join(prohib_lines))

    # §5.1 Intentional Mysteries — 테이블 전체를 추출
    # 의도적 미스터리를 브리프에 포함해야 작가가 플롯 홀로 오인하지 않는다
    mystery_match = re.search(
        r"### 5\.1\s*(?:Intentional Mysteries|의도적 미스터리|의도적 비밀).*?\n(.*?)(?=\n## \d|\n### \d|\n---\n|$)",
        content,
        re.DOTALL,
    )
    if mystery_match:
        mystery_text = mystery_match.group(1).strip()
        # 테이블 행만 추출 (설명 blockquote 포함)
        mystery_lines = []
        for line in mystery_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") or stripped.startswith(">"):
                mystery_lines.append(stripped)
        if mystery_lines:
            parts.append(
                "### 의도적 미스터리 (플롯홀 아님)\n\n"
                + "\n".join(mystery_lines)
            )

    # 호칭/어투 매트릭스 — 테이블만 추출
    speech_match = re.search(
        r"### 8\.1 호칭/어투 매트릭스\s*\n(.*?)(?=\n### 8\.2|$)",
        content,
        re.DOTALL,
    )
    if speech_match:
        # 테이블 행만 추출
        table_lines = [
            l for l in speech_match.group(1).strip().splitlines()
            if l.startswith("|")
        ]
        parts.append("### 호칭/어투\n\n" + "\n".join(table_lines))

    return "\n\n".join(parts) if parts else "(규칙 없음)"


def _extract_style_rules(content: str) -> str:
    """settings/01-style-guide.md에서 핵심 규칙만 추출한다.

    Voice Profile (§0), 시점, 문장 리듬 기본 원칙을 가져온다.
    대표 문단(§0.3)은 verbatim 포함 — 요약하면 보이스 앵커링 효과가 사라진다.
    """
    if not content:
        return ""

    parts: list[str] = []

    # Voice Profile §0 — 서술 온도 + 보이스 우선순위 + 대표 문단 (verbatim)
    voice_match = re.search(
        r"## 0\. Voice Profile.*?\n(.*?)(?=\n## 1\.|$)",
        content,
        re.DOTALL,
    )
    if voice_match:
        voice_text = voice_match.group(1).strip()
        # HTML 주석 제거 (예시 블록)
        voice_text = re.sub(r"<!--.*?-->", "", voice_text, flags=re.DOTALL)
        # placeholder 미채워진 경우 건너뜀 ({{가 본문에 남아있으면 skip)
        if voice_text and "{{" not in voice_text:
            parts.append("### Voice Profile\n\n" + voice_text)

    # 시점 섹션
    pov_match = re.search(
        r"## 1\. 시점.*?\n(.*?)(?=\n## \d|$)", content, re.DOTALL
    )
    if pov_match:
        # 코드블록 제거
        text = re.sub(r"```.*?```", "", pov_match.group(1), flags=re.DOTALL)
        parts.append("**시점**: " + text.strip()[:300])

    # 문장 리듬 기본 원칙 (lean: "우선 원칙", legacy: "기본 원칙")
    rhythm_match = re.search(
        r"### (?:\d+\.\d+\s+)?(?:우선 원칙|기본 원칙)\s*\n(.*?)(?=\n###|\n## |$)",
        content,
        re.DOTALL,
    )
    if rhythm_match:
        parts.append("**문장 리듬**: " + rhythm_match.group(1).strip()[:300])

    return "\n\n".join(parts)


def _extract_notation_rules(
    worldbuilding: str, claude_md: str
) -> str:
    """worldbuilding과 CLAUDE.md에서 표기/단위 규칙을 추출한다.

    시대 판별: worldbuilding에 현대/SF 키워드가 있으면 비현대 숫자 규칙을 주입하지 않는다.
    """
    rules: list[str] = []

    # worldbuilding에서 시대 배경 판별
    is_modern = False
    era_desc = ""
    if worldbuilding:
        era_match = re.search(
            r"(?:시대|배경|세계관).*?[:：]\s*(.+)", worldbuilding
        )
        if era_match:
            era_desc = era_match.group(1).strip()[:100]
            rules.append(f"- 세계관: {era_desc}")

        premodern_keywords = ["전근대", "사극", "무협", "조선", "고려"]
        modern_keywords = [
            "현대",
            "sf",
            "미래",
            "21세기",
            "20세기",
            "sci-fi",
            "science fiction",
            "cyberpunk",
        ]
        wb_lower = worldbuilding.lower()
        if any(kw in wb_lower for kw in premodern_keywords):
            is_modern = False
        elif any(kw in wb_lower for kw in modern_keywords):
            is_modern = True

    # CLAUDE.md에서 비현대 숫자 표기 규칙 — 비현대 배경에서만 주입
    if not is_modern:
        if "아라비아 숫자" in claude_md:
            rules.append("- 비현대 배경: 아라비아 숫자 금지, 한글 수사 사용")
        if "소수점" in claude_md:
            rules.append("- 소수점 금지 (1.5장→한 장 반)")
        if "사흘" in claude_md:
            rules.append("- 3일→사흘, 7일→이레, 10일→열흘, 15일→보름")
    else:
        rules.append("- 현대/SF 배경: 아라비아 숫자, 현대 단위, 외래어 자연스럽게 허용")

    return "\n".join(rules) if rules else ""


def _extract_episode_goals(
    novel_dir: str, episode_number: int
) -> str:
    """plot 파일에서 해당 에피소드의 목표/내용을 추출한다."""
    plot_dir = Path(novel_dir) / "plot"
    if not plot_dir.exists():
        return "(플롯 파일 없음)"

    for plot_file in _iter_plot_files(novel_dir):
        section = _extract_episode_plot_block(
            _safe_read(plot_file), episode_number
        )
        if not section:
            continue
        if len(section) > 1500:
            section = section[:1500] + "\n...(생략)"

        return section.strip()

    return "(해당 에피소드 플롯 없음)"


def _extract_all_tracked_characters(tracker_path: str | Path) -> list[str]:
    """character-tracker.md에서 모든 캐릭터 이름을 추출한다 (확장 폴백용)."""
    content = _safe_read(tracker_path)
    if not content:
        return []
    names = re.findall(r"^### (.+)", content, re.MULTILINE)
    return [_clean_character_name(n) for n in names[:10]]  # 최대 10명


def _extract_global_knowledge(content: str) -> str:
    """knowledge-map에서 캐릭터 무관하게 중요한 정보를 추출한다.

    '비밀', '오해', '금지', '폭로', '미공개' 등의 키워드가 포함된 행은
    등장인물 필터와 무관하게 항상 포함한다.
    """
    if not content:
        return ""

    global_keywords = ["비밀", "오해", "금지", "폭로", "미공개", "함정", "거짓"]
    lines = content.splitlines()

    # 헤더 행 찾기
    header_line_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|") and "정보" in line:
            header_line_idx = i
            break

    if header_line_idx is None:
        return ""

    result: list[str] = [lines[header_line_idx]]
    # 구분선
    if header_line_idx + 1 < len(lines):
        result.append(lines[header_line_idx + 1])

    for line in lines[header_line_idx + 2:]:
        if not line.startswith("|"):
            continue
        first_col = line.split("|")[1].strip() if len(line.split("|")) > 1 else ""
        if any(kw in first_col for kw in global_keywords):
            result.append(line)

    if len(result) <= 2:
        return ""
    return "### 전역 핵심 정보 (캐릭터 무관)\n\n" + "\n".join(result)


def _extract_relationship_turning_points(content: str) -> str:
    """relationship-log에서 관계 전환점을 추출한다.

    '반전', '단절', '화해', '배신', '고백', '결별' 등의 키워드가 있는 항목.
    """
    if not content:
        return ""

    turning_keywords = ["반전", "단절", "화해", "배신", "고백", "결별",
                        "전환", "변화", "갈등", "결렬"]
    lines = content.splitlines()
    result: list[str] = []

    for line in lines:
        if not line.startswith("|"):
            continue
        if any(kw in line for kw in turning_keywords):
            # 200자 제한
            if len(line) > 200:
                result.append(line[:200] + "...")
            else:
                result.append(line)

    if not result:
        return ""
    return "### 관계 전환점\n\n" + "\n".join(result[-5:])


# ─── Main Compiler ─────────────────────────────────────────


def _compile_brief(
    novel_dir: str,
    episode_number: int,
    characters: Optional[list[str]] = None,
) -> str:
    """소설 프로젝트 파일들을 읽어 집필 브리프를 생성한다.

    Parameters
    ----------
    novel_dir : str
        소설 폴더 절대 경로 (예: /root/novel/no-title-015)
    episode_number : int
        집필할 에피소드 번호
    characters : list[str] | None
        이번 화 등장인물 목록.
        None이면 plot 파일에서 자동 추출을 시도한다.

    Returns
    -------
    str
        구조화된 마크다운 브리프 문서 (~4-6KB)
    """
    novel_path = Path(novel_dir)
    summaries = novel_path / "summaries"
    _append_runtime_event(
        novel_dir,
        "compile_brief_start",
        episode=episode_number,
    )

    # ── 등장인물 결정 ──
    char_confidence = "high"
    if not characters:
        characters = _extract_characters_from_plot(novel_dir, episode_number)
        if characters:
            char_confidence = "medium"  # plot에서 자동 추출
        else:
            # 확장 폴백: 직전화 등장인물 + 아크 핵심 인물
            characters = _extract_characters_from_episode_log(
                novel_dir, episode_number
            )
            if characters:
                char_confidence = "low"  # episode-log 기반 추정
            else:
                # 최종 폴백: 전체 캐릭터 포함 (축소가 아니라 확장)
                characters = _extract_all_tracked_characters(
                    summaries / "character-tracker.md"
                )
                char_confidence = "fallback"

    # ── 파일 읽기 ──
    running_context = _safe_read_logged(
        novel_dir,
        summaries / "running-context.md",
        "running-context",
        required=True,
    )
    character_tracker = _safe_read_logged(
        novel_dir,
        summaries / "character-tracker.md",
        "character-tracker",
        required=True,
    )
    knowledge_map = _safe_read_logged(
        novel_dir,
        summaries / "knowledge-map.md",
        "knowledge-map",
    )
    relationship_log = _safe_read_logged(
        novel_dir,
        summaries / "relationship-log.md",
        "relationship-log",
    )
    promise_tracker = _safe_read_logged(
        novel_dir,
        summaries / "promise-tracker.md",
        "promise-tracker",
    )
    foreshadowing = _safe_read_logged(
        novel_dir,
        novel_path / "plot" / "foreshadowing.md",
        "foreshadowing",
    )
    episode_log = _safe_read_logged(
        novel_dir,
        summaries / "episode-log.md",
        "episode-log",
        required=True,
    )
    dialogue_log = _safe_read_logged(
        novel_dir,
        summaries / "dialogue-log.md",
        "dialogue-log",
    )
    claude_md = _safe_read_logged(
        novel_dir,
        novel_path / "CLAUDE.md",
        "claude-md",
        required=True,
    )
    style_guide = _safe_read_logged(
        novel_dir,
        novel_path / "settings" / "01-style-guide.md",
        "style-guide",
        required=True,
    )
    style_lexicon = _safe_read_logged(
        novel_dir,
        summaries / "style-lexicon.md",
        "style-lexicon",
    )
    decision_log = _safe_read_logged(
        novel_dir,
        summaries / "decision-log.md",
        "decision-log",
    )
    watchlist = _safe_read_logged(
        novel_dir,
        summaries / "repetition-watchlist.md",
        "repetition-watchlist",
    )

    # ── 각 섹션 생성 ──
    sections: list[str] = []

    # 0. 헤더
    sections.append(f"# Writing Brief — {episode_number}화")
    confidence_label = {
        "high": "", "medium": " (plot 기반 자동 감지)",
        "low": " ⚠️ (episode-log 추정, 신규 인물 누락 가능)",
        "fallback": " ⚠️⚠️ (자동 감지 실패, 전체 캐릭터 포함)"
    }
    sections.append(
        f"**등장인물**: {', '.join(characters)}"
        f"{confidence_label.get(char_confidence, '')}"
    )

    goals = _extract_episode_goals(novel_dir, episode_number)
    prev_anchor = _extract_previous_episode_anchor(novel_dir, episode_number)
    live_cues = _build_live_drafting_cues(
        goals=goals,
        prev_anchor=prev_anchor,
        running_context=running_context,
        style_guide=style_guide,
        style_lexicon=style_lexicon,
        dialogue_log=dialogue_log,
        relationship_log=relationship_log,
        watchlist=watchlist,
        decision_log=decision_log,
    )
    if live_cues:
        sections.append(f"## Live Drafting Cues\n\n{live_cues}")

    # 1. 이번 화 목표
    sections.append(f"## 이번 화 목표\n\n{goals}")

    # 1.5. 직전 화 오프닝 앵커 (/clear 여부와 무관하게 중요)
    if prev_anchor:
        sections.append(f"## 직전 화 직결 앵커\n\n{prev_anchor}")

    # 2. 최근 맥락 — 현재 상태 + 최근 아크 요약만 (압축 흐름은 생략)
    if running_context:
        rc_parts: list[str] = []
        # "## 현재 상태" 또는 "## Current Status" 섹션 추출
        current_match = re.search(
            r"## (?:현재 상태|현재 시점|Current Status|Current State)\s*\n(.*?)(?=\n## |$)",
            running_context,
            re.DOTALL,
        )
        if current_match:
            rc_parts.append(current_match.group(1).strip())

        # 다음 화 오프닝 직결 상태
        immediate_match = re.search(
            r"## (?:직전 화 직결 상태|Immediate Carry-Forward|Carry-Forward)\s*\n(.*?)(?=\n## |$)",
            running_context,
            re.DOTALL,
        )
        if immediate_match:
            rc_parts.append(
                "**직결 상태**:\n" + immediate_match.group(1).strip()
            )

        # "## 압축 흐름" / "## Recent Events" 등
        flow_match = re.search(
            r"## (?:압축 흐름|전체 흐름 압축|전체 흐름 \(압축\)|Recent Events|Compressed Flow)\s*\n(.*?)(?=\n## |$)",
            running_context,
            re.DOTALL,
        )
        if flow_match:
            flow_text = flow_match.group(1).strip()
            arc_blocks = re.split(r"(?=^### )", flow_text, flags=re.MULTILINE)
            non_empty = [b for b in arc_blocks if b.strip()]
            if non_empty and any(
                block.lstrip().startswith("### ") for block in non_empty
            ):
                rc_parts.append(
                    "**최근 흐름**:\n" + "\n".join(non_empty[-2:]).strip()
                )
            else:
                bullets = [
                    line.strip()
                    for line in flow_text.splitlines()
                    if line.strip().startswith("-")
                ]
                if bullets:
                    rc_parts.append(
                        "**최근 흐름**:\n" + "\n".join(bullets[-3:])
                    )
                elif flow_text:
                    clipped = flow_text[:700]
                    if len(flow_text) > 700:
                        clipped += "\n...(생략)"
                    rc_parts.append("**최근 흐름**:\n" + clipped)

        # "## 캐릭터 최종 상태" 테이블 — 등장인물만 필터
        char_table_match = re.search(
            r"## (?:캐릭터 최종 상태|Character End State|Character State)\s*\n(.*?)(?=\n## |$)",
            running_context,
            re.DOTALL,
        )
        if char_table_match:
            table = char_table_match.group(1).strip()
            table_lines = table.splitlines()
            filtered_table = []
            for tl in table_lines:
                if not tl.startswith("|"):
                    continue
                if all(c in "-| " for c in tl):
                    filtered_table.append(tl)
                elif "캐릭터" in tl and "상태" in tl:
                    filtered_table.append(tl)
                elif any(char in tl for char in characters):
                    filtered_table.append(tl)
            if filtered_table:
                rc_parts.append("\n".join(filtered_table))

        # "## 복선 최종 상태" 섹션 — 테이블만
        foreshadow_match = re.search(
            r"## (?:복선 최종 상태|Foreshadowing End State)\s*\n(.*?)(?=\n## |$)",
            running_context,
            re.DOTALL,
        )
        if foreshadow_match:
            rc_parts.append(foreshadow_match.group(1).strip())

        rc_body = "\n\n".join(rc_parts)
        if not rc_body:
            rc_body = running_context[:1200]
            if len(running_context) > 1200:
                rc_body += "\n...(생략)"
        sections.append(f"## 최근 맥락\n\n{rc_body}")
    else:
        sections.append("## 최근 맥락\n\n(파일 없음)")

    # 3. 등장인물 설정 슬라이스 (settings/03-characters.md에서 핵심만 — 앵커 역할)
    slice_chars = characters
    if not slice_chars:
        slice_chars = _extract_all_tracked_characters(
            summaries / "character-tracker.md"
        )
    char_slice = _extract_character_slice(novel_dir, slice_chars)
    if char_slice:
        sections.append(f"## 등장인물 설정\n\n{char_slice}")

    # 3.5. 최근 대화 운용 (dialogue-log.md — 이탈 행 + role-only 행)
    filtered_dialogue = _filter_dialogue_log(
        dialogue_log, characters, episode_number
    )
    if filtered_dialogue:
        sections.append(f"## 최근 대화 운용\n\n{filtered_dialogue}")

    # 4. 등장인물 상태
    filtered_chars = _filter_character_tracker(
        character_tracker, characters
    )
    sections.append(f"## 등장인물 상태\n\n{filtered_chars}")

    # 5. 정보 보유 현황
    filtered_knowledge = _filter_knowledge_map(knowledge_map, characters)
    sections.append(f"## 정보 보유 현황\n\n{filtered_knowledge}")

    # 5. 관계 현황
    filtered_relations = _filter_relationship_log(
        relationship_log, characters
    )
    sections.append(f"## 관계 현황\n\n{filtered_relations}")

    # 6. 활성 약속 (항상 전체 포함 — 캐릭터 필터 없음)
    filtered_promises = _filter_promise_tracker(promise_tracker)
    sections.append(f"## 활성 약속\n\n{filtered_promises}")

    # 7. 활성 복선 (항상 전체 포함 — 캐릭터 필터 없음)
    filtered_foreshadow = _filter_foreshadowing(foreshadowing)
    sections.append(f"## 활성 복선\n\n{filtered_foreshadow}")

    # 7.5. 전역 컨텍스트 (캐릭터 무관 핵심 정보)
    global_parts: list[str] = []
    global_knowledge = _extract_global_knowledge(knowledge_map)
    if global_knowledge:
        global_parts.append(global_knowledge)
    turning_points = _extract_relationship_turning_points(relationship_log)
    if turning_points:
        global_parts.append(turning_points)
    # 프로젝트 단위 의도적 규칙 이탈 기록
    if decision_log:
        # 테이블 행이 있는 경우만 포함 (빈 템플릿 제외)
        table_rows = [
            line for line in decision_log.splitlines()
            if line.startswith("|") and not all(c in "-| " for c in line)
            and "규칙" not in line  # 헤더 제외
        ]
        if table_rows:
            global_parts.append(
                "### 프로젝트 규칙 이탈\n\n"
                + decision_log.split("\n\n", 1)[-1].strip()
            )
    if global_parts:
        sections.append(
            "## 전역 컨텍스트\n\n" + "\n\n".join(global_parts)
        )

    # 8. 최근 에피소드
    recent_episodes = _extract_last_n_episodes(
        episode_log, n=3, before_episode=episode_number
    )
    sections.append(f"## 최근 에피소드\n\n{recent_episodes}")

    # 9. 핵심 규칙 (상시 포함 — settings/ 직접 읽기 대체)
    rules = _extract_claude_md_rules(claude_md)
    style = _extract_style_rules(style_guide)
    rules_combined = rules
    if style:
        rules_combined += "\n\n### 문체\n\n" + style

    # 표기 규칙 추출 (settings/04-worldbuilding.md에서 숫자/단위 규칙)
    worldbuilding = _safe_read(
        novel_path / "settings" / "04-worldbuilding.md"
    )
    notation_rules = _extract_notation_rules(worldbuilding, claude_md)
    if notation_rules:
        rules_combined += "\n\n### 표기 규칙\n\n" + notation_rules

    sections.append(f"## 핵심 규칙\n\n{rules_combined}")

    # 9.5. 연속성 불변 조건 + 타임라인 (settings/05-continuity.md에서 추출)
    continuity = _safe_read(novel_path / "settings" / "05-continuity.md")
    if continuity:
        cont_parts = []
        # 불변 조건 표 추출 (헤딩과 테이블 사이에 blockquote/빈줄이 있을 수 있음)
        inv_match = re.search(
            r"### Continuity Invariants.*?\n((?:>.*\n|\s*\n)*)((?:\|.+\n)+)",
            continuity,
        )
        if inv_match:
            inv_text = inv_match.group(2).strip()
            # 플레이스홀더 행 제외
            inv_lines = [
                l for l in inv_text.splitlines()
                if l.startswith("|") and "{{" not in l
            ]
            if inv_lines:
                cont_parts.append(
                    "### 불변 조건 (반드시 준수)\n\n"
                    + "\n".join(inv_lines)
                )

        # 타임라인 마커 추출 (헤딩과 테이블 사이에 blockquote/빈줄 가능)
        tm_match = re.search(
            r"### Key Timeline Markers.*?\n((?:>.*\n|\s*\n)*)((?:\|.+\n)+)",
            continuity,
        )
        if tm_match:
            tm_text = tm_match.group(2).strip()
            tm_lines = [
                l for l in tm_text.splitlines()
                if l.startswith("|") and "{{" not in l
            ]
            if tm_lines:
                cont_parts.append(
                    "### 핵심 타임라인\n\n"
                    + "\n".join(tm_lines)
                )

        if cont_parts:
            sections.append("## 연속성 불변 조건\n\n" + "\n\n".join(cont_parts))

    # 10. (등장인물 설정은 섹션 3으로 이동됨)

    # 10.5. 에피소드 구조/분량 (settings/02-episode-structure.md에서 핵심만)
    ep_structure = _safe_read(novel_path / "settings" / "02-episode-structure.md")
    if ep_structure:
        # "## 4. 분량 가이드" 또는 "분량" 섹션의 테이블 전체 추출
        table_match = re.search(
            r"## \d+\.\s*분량.*?\n\s*\n?((?:\|.+\n)+)",
            ep_structure,
        )
        if table_match:
            sections.append("## 분량/구조\n\n" + table_match.group(1).strip())

    # 11. 어휘 치환 사전 (style-lexicon — 작고 전역적이므로 전체 포함)
    if style_lexicon:
        # 데이터 행이 있는 경우만 포함 (빈 템플릿 제외)
        data_rows = [
            line for line in style_lexicon.splitlines()
            if line.startswith("|") and "→" in line
        ]
        if data_rows:
            sections.append(f"## 어휘 치환 사전\n\n{style_lexicon.strip()}")

    # 12. 반복 패턴 감시 목록 (repetition-watchlist — WATCH/HIGH만 압축)
    if watchlist:
        watch_lines = []
        in_watch_section = False
        for line in watchlist.splitlines():
            stripped = line.strip()
            # "## 감시 중 (WATCH)" 또는 WATCH/HIGH가 포함된 섹션만
            if "감시 중" in stripped or "WATCH" in stripped or "HIGH" in stripped:
                in_watch_section = True
            elif stripped.startswith("## 면책") or stripped.startswith("## 해결"):
                in_watch_section = False
            # 데이터 행 추출 (헤더/구분선 제외, 감시 섹션 내부만)
            if in_watch_section and stripped.startswith("|") and not stripped.startswith("| ID") and not stripped.startswith("|--"):
                watch_lines.append(stripped)
        if watch_lines:
            sections.append(
                "## 반복 패턴 주의 (WATCH/HIGH)\n\n"
                "| ID | 유형 | 패턴 | 현재 빈도 | 허용 한도 | 비고 |\n"
                "|----|----|------|---------|---------|------|\n"
                + "\n".join(watch_lines[:15])  # 최대 15행
            )

    # 14. 용어 온보딩 경고 (미설명 + 기한 임박/초과만)
    term_onboarding = _safe_read_logged(
        novel_dir,
        summaries / "term-onboarding.md",
        "term-onboarding",
    )
    if term_onboarding:
        overdue_lines = []
        for line in term_onboarding.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and "미설명" in stripped:
                overdue_lines.append(stripped)
        if overdue_lines:
            sections.append(
                "## 용어 온보딩 경고\n\n"
                + "\n".join(overdue_lines[:10])
            )

    brief = "\n\n".join(sections)

    # 최종 크기 체크 (정보성)
    size_kb = len(brief.encode("utf-8")) / 1024
    header_line = (
        f"> 브리프 크기: {size_kb:.1f}KB | "
        f"원본 합계: ~{_estimate_source_size(novel_dir):.0f}KB"
    )
    sections.insert(1, header_line)

    final_brief = "\n\n".join(sections)
    _write_brief_snapshot(novel_dir, episode_number, final_brief)
    _append_runtime_event(
        novel_dir,
        "compile_brief_complete",
        episode=episode_number,
        size_bytes=len(final_brief.encode("utf-8")),
    )
    return final_brief


def _estimate_source_size(novel_dir: str) -> float:
    """소스 파일들의 대략적인 합산 크기를 KB로 반환한다."""
    total = 0
    paths = [
        "summaries/running-context.md",
        "summaries/character-tracker.md",
        "summaries/knowledge-map.md",
        "summaries/relationship-log.md",
        "summaries/promise-tracker.md",
        "summaries/episode-log.md",
        "plot/foreshadowing.md",
        "CLAUDE.md",
        "settings/01-style-guide.md",
    ]
    for p in paths:
        full = Path(novel_dir) / p
        if full.exists():
            total += full.stat().st_size
    return total / 1024


# ─── MCP Tool Wrapper ─────────────────────────────────────


def register_compile_brief(mcp_instance):
    """MCP 서버 인스턴스에 compile_brief 도구를 등록한다.

    사용법:
        from compile_brief import register_compile_brief
        register_compile_brief(mcp)
    """

    @mcp_instance.tool()
    async def compile_brief(
        novel_dir: str,
        episode_number: int,
        characters: str = "",
    ) -> str:
        """소설 프로젝트 파일(~300KB+)을 분석하여 해당 에피소드 집필에
        필요한 핵심 정보만 담긴 압축 브리프(~4-6KB)를 생성한다.

        Parameters
        ----------
        novel_dir : str
            소설 폴더 절대 경로 (예: /root/novel/no-title-015)
        episode_number : int
            집필할 에피소드 번호
        characters : str
            쉼표로 구분된 등장인물 이름 (예: "윤서하,리라,이정하").
            비워두면 plot 파일에서 자동 추출한다.
        """
        char_list: list[str] | None = None
        if characters.strip():
            char_list = [c.strip() for c in characters.split(",") if c.strip()]

        try:
            result = _compile_brief(novel_dir, episode_number, char_list)
            return result
        except Exception as e:
            return f"[ERROR] 브리프 생성 실패: {type(e).__name__}: {e}"


# ─── CLI Entry Point ──────────────────────────────────────


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: python compile_brief.py <novel_dir> <episode_number> "
            "[character1,character2,...]"
        )
        sys.exit(1)

    novel_dir = sys.argv[1]
    episode_number = int(sys.argv[2])
    chars = None
    if len(sys.argv) > 3:
        chars = [c.strip() for c in sys.argv[3].split(",")]

    brief = _compile_brief(novel_dir, episode_number, chars)
    print(brief)
