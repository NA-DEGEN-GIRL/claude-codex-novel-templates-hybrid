#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# Conditional+Logged summaries (batch-supervisor.md 3b-post step 6).
# 각 파일이 프로젝트에 존재하면 action-log에 updated/skipped 판단 기록이 있어야 한다.
# 파일이 없는 프로젝트(예: 한자 미사용 → hanja-glossary 없음)는 요구하지 않는다.
CONDITIONAL_LOGGED_STEMS = (
    "promise-tracker",
    "knowledge-map",
    "relationship-log",
    "foreshadowing",
    "decision-log",
    "dialogue-log",
    "desire-state",
    "signature-moves",
    "style-lexicon",
    "term-onboarding",
    "hanja-glossary",
)

# running-context.md의 직전 화 직결 상태 섹션 헤더 후보 (영문/국문 병기).
CARRY_FORWARD_HEADINGS = ("Immediate Carry-Forward", "직전 화 직결")


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _append_event(novel_dir: Path, event: str, **payload: object) -> None:
    path = novel_dir / "tmp" / "run-metadata" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": _utc_now(), "event": event, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _git_lines(novel_dir: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(novel_dir), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _find_chapter_path(files: list[str], episode: int) -> str | None:
    suffix = f"chapter-{episode:02d}.md"
    for item in files:
        if item.endswith(suffix) and item.startswith("chapters/"):
            return item
    return None


def _read_staged_file(novel_dir: Path, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(novel_dir), "show", f":{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _added_lines(novel_dir: Path, path: str, mode: str) -> str:
    """staged(diff --cached) 또는 committed(show HEAD) diff에서 추가된(+) 라인만 모아 반환.

    append-only 로그(review-log/action-log)에서 "이번 커밋이 실제로 무엇을 기록했는가"를
    본다. diff를 못 읽으면 빈 문자열을 반환하고, 호출부가 "기록 없음"으로 처리한다.
    """
    if mode == "staged":
        args = ["diff", "--cached", "-U0", "--", path]
    else:
        args = ["show", "-U0", "--format=", "HEAD", "--", path]
    try:
        result = subprocess.run(
            ["git", "-C", str(novel_dir), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return ""
    added: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
    return "\n".join(added)


def _full_content(novel_dir: Path, path: str, mode: str) -> str | None:
    """staged 또는 working-tree 전체 내용. 읽기 실패 시 None."""
    try:
        if mode == "staged":
            return _read_staged_file(novel_dir, path)
        return (novel_dir / path).read_text(encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _check_review_log_header(added: str, episode: int) -> str | None:
    """staged review-log diff에 이번 화 헤더(### {N}화 ...)가 append됐는지.

    실제 기록 형식: `### {N}화 ({mode}) — {date}` (unified-reviewer.md Note 9,
    summaries/review-log.md 형식 주석). 화번호는 zero-pad 없음.
    """
    if re.search(rf"(?m)^\s*#{{2,4}}\s*{episode}\s*화\b", added):
        return None
    return f"review_log_no_header_for_ep{episode}(need '### {episode}화')"


def _check_action_log_tokens(novel_dir: Path, added: str) -> str | None:
    """staged action-log diff에 Conditional+Logged 파일별 updated/skipped 토큰 확인.

    형식: `{파일}: updated N건` 또는 `{파일}: skipped (사유)` (batch-supervisor 3b-post).
    파일명은 .md 유무 무관. 프로젝트에 존재하는 로그 파일만 대상으로 한다.
    """
    missing: list[str] = []
    for stem in CONDITIONAL_LOGGED_STEMS:
        if not (novel_dir / "summaries" / f"{stem}.md").exists():
            continue
        pattern = rf"{re.escape(stem)}(?:\.md)?\s*[:：\-–]?\s*(updated|skipped)"
        if not re.search(pattern, added, re.IGNORECASE):
            missing.append(stem)
    if missing:
        return "action_log_no_status_for=" + ",".join(missing)
    return None


def _check_carry_forward(content: str) -> str | None:
    """running-context에 Immediate Carry-Forward(또는 직전 화 직결 상태) 섹션 + bullet>=3."""
    lines = content.splitlines()
    section_start: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s", line) and any(
            key in line for key in CARRY_FORWARD_HEADINGS
        ):
            section_start = i
            break
    if section_start is None:
        return "running_context_no_carry_forward_section"

    bullets = 0
    for line in lines[section_start + 1:]:
        if re.match(r"^#{1,6}\s", line):
            break
        if re.match(r"^\s*[-*+]\s+\S", line):
            bullets += 1
    if bullets < 3:
        return f"running_context_carry_forward_bullets={bullets}(need>=3)"
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    parser.add_argument("--episode", required=True, type=int)
    parser.add_argument("--mode", choices={"staged", "head"}, default="staged")
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    # required stage set: 본문 후처리 3종 + review 판정 로그.
    required_files = {
        "summaries/running-context.md",
        "summaries/episode-log.md",
        "summaries/character-tracker.md",
        "summaries/action-log.md",
        "summaries/review-log.md",
    }

    try:
        if args.mode == "staged":
            changed = _git_lines(novel_dir, "diff", "--cached", "--name-only")
        else:
            changed = _git_lines(
                novel_dir,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD",
            )
    except subprocess.CalledProcessError as exc:
        print(f"GATE_FAIL git_error={exc}", file=sys.stderr)
        return 2

    changed_set = set(changed)
    chapter_path = _find_chapter_path(changed, args.episode)
    missing = sorted(required_files - changed_set)
    reasons: list[str] = []

    if not changed:
        reasons.append("no_changed_files")
    if chapter_path is None:
        reasons.append(f"missing_chapter_{args.episode:02d}")
    if missing:
        reasons.append("missing_required=" + ",".join(missing))

    if chapter_path is not None:
        try:
            chapter_text = (
                _read_staged_file(novel_dir, chapter_path)
                if args.mode == "staged"
                else (novel_dir / chapter_path).read_text(encoding="utf-8")
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            reasons.append(f"chapter_read_error={type(exc).__name__}")
        else:
            if "### EPISODE_META" not in chapter_text:
                reasons.append("missing_episode_meta")

    # (1) review-log: 이번 화 판정 헤더가 append됐는가.
    if "summaries/review-log.md" in changed_set:
        review_added = _added_lines(novel_dir, "summaries/review-log.md", args.mode)
        header_reason = _check_review_log_header(review_added, args.episode)
        if header_reason:
            reasons.append(header_reason)

    # (2) action-log: Conditional+Logged 파일별 updated/skipped 판단 기록이 있는가.
    if "summaries/action-log.md" in changed_set:
        action_added = _added_lines(novel_dir, "summaries/action-log.md", args.mode)
        token_reason = _check_action_log_tokens(novel_dir, action_added)
        if token_reason:
            reasons.append(token_reason)

    # (3) running-context: 직전 화 직결 상태 섹션 + bullet>=3.
    if "summaries/running-context.md" in changed_set:
        rc_content = _full_content(novel_dir, "summaries/running-context.md", args.mode)
        if rc_content is None:
            reasons.append("running_context_read_error")
        else:
            cf_reason = _check_carry_forward(rc_content)
            if cf_reason:
                reasons.append(cf_reason)

    if reasons:
        _append_event(
            novel_dir,
            "review_done_gate_failed",
            episode=args.episode,
            mode=args.mode,
            reasons=reasons,
        )
        print("GATE_FAIL " + " ".join(reasons))
        return 1

    _append_event(
        novel_dir,
        "review_done_gate_passed",
        episode=args.episode,
        mode=args.mode,
        chapter=chapter_path,
        changed_files=len(changed),
    )
    print(
        f"GATE_OK episode={args.episode:02d} mode={args.mode} chapter={chapter_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
