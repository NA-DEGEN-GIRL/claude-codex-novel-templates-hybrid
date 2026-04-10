#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    parser.add_argument("--episode", required=True, type=int)
    parser.add_argument("--mode", choices={"staged", "head"}, default="staged")
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    required_files = {
        "summaries/running-context.md",
        "summaries/episode-log.md",
        "summaries/character-tracker.md",
        "summaries/action-log.md",
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

    chapter_path = _find_chapter_path(changed, args.episode)
    missing = sorted(required_files - set(changed))
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
