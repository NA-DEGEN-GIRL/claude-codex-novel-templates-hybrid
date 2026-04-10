#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path


def _load_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _summary(events: list[dict]) -> dict[str, object]:
    event_counts = Counter(event.get("event", "unknown") for event in events)
    send_counts = Counter(
        event.get("status", "unknown")
        for event in events
        if event.get("event") in {"tmux_send_codex_result", "tmux_send_claude_result"}
    )
    wait_counts = Counter(
        event.get("status", "unknown")
        for event in events
        if event.get("event") == "tmux_wait_sentinel_result"
    )
    brief_sizes = [
        int(event["size_bytes"])
        for event in events
        if event.get("event") == "compile_brief_complete" and "size_bytes" in event
    ]
    return {
        "total_events": len(events),
        "event_counts": dict(event_counts),
        "send_result_counts": dict(send_counts),
        "wait_result_counts": dict(wait_counts),
        "read_missing": event_counts.get("read_missing", 0),
        "read_error": event_counts.get("read_error", 0),
        "review_gate_passed": event_counts.get("review_done_gate_passed", 0),
        "review_gate_failed": event_counts.get("review_done_gate_failed", 0),
        "hold_checks": event_counts.get("hold_check_result", 0),
        "brief_runs": len(brief_sizes),
        "avg_brief_size_bytes": round(statistics.mean(brief_sizes), 2) if brief_sizes else 0,
        "max_brief_size_bytes": max(brief_sizes) if brief_sizes else 0,
    }


def _markdown(summary: dict[str, object]) -> str:
    lines = [
        "## Runtime Metrics",
        "",
        f"- total_events: {summary['total_events']}",
        f"- read_missing: {summary['read_missing']}",
        f"- read_error: {summary['read_error']}",
        f"- review_gate_passed: {summary['review_gate_passed']}",
        f"- review_gate_failed: {summary['review_gate_failed']}",
        f"- hold_checks: {summary['hold_checks']}",
        f"- brief_runs: {summary['brief_runs']}",
        f"- avg_brief_size_bytes: {summary['avg_brief_size_bytes']}",
        f"- max_brief_size_bytes: {summary['max_brief_size_bytes']}",
        "",
        "### tmux send results",
    ]
    send_counts = summary["send_result_counts"]
    if send_counts:
        for key, value in sorted(send_counts.items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- (없음)")
    lines.append("")
    lines.append("### tmux wait results")
    wait_counts = summary["wait_result_counts"]
    if wait_counts:
        for key, value in sorted(wait_counts.items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- (없음)")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    parser.add_argument("--format", choices={"markdown", "json"}, default="markdown")
    args = parser.parse_args(argv[1:])

    event_path = Path(args.novel_dir) / "tmp" / "run-metadata" / "events.jsonl"
    summary = _summary(_load_events(event_path))
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
