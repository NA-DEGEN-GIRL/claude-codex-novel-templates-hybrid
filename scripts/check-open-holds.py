#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


FIELD_ALIASES = {
    "hold_route": "hold_route",
    "scope": "scope",
    "출처": "source",
    "source": "source",
    "문제": "issue",
    "issue": "issue",
    "보상 계획": "plan",
    "plan": "plan",
    "target": "target",
    "latest-safe-resolution": "latest_safe_resolution",
    "status": "status",
    "blocker": "blocker",
}


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


def _parse_hold_sections(text: str) -> list[dict[str, str]]:
    sections = re.split(r"(?=^### HOLD-)", text, flags=re.MULTILINE)
    holds: list[dict[str, str]] = []
    for section in sections:
        section = section.strip()
        if not section.startswith("### HOLD-"):
            continue

        header = section.splitlines()[0]
        match = re.match(r"###\s+(HOLD-[A-Za-z0-9_-]+)", header)
        if not match:
            continue

        hold: dict[str, str] = {"id": match.group(1)}
        for line in section.splitlines()[1:]:
            stripped = line.strip()
            if not stripped.startswith("- ") or ":" not in stripped:
                continue
            key, value = stripped[2:].split(":", 1)
            normalized = FIELD_ALIASES.get(key.strip(), key.strip())
            hold[normalized] = value.strip()
        holds.append(hold)
    return holds


def _resolution_episode(value: str) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d+)화", value)
    if not match:
        return None
    return int(match.group(1))


def _is_blocker(hold: dict[str, str]) -> bool:
    explicit = hold.get("blocker", "").lower()
    if explicit in {"yes", "true"}:
        return True
    if explicit in {"no", "false"}:
        return False
    return hold.get("hold_route") in {"retro-fix", "plot-repair", "user-escalation"}


def _line_summary(holds: list[dict[str, object]]) -> str:
    total = len(holds)
    overdue = sum(1 for hold in holds if hold.get("is_overdue"))
    blockers = sum(1 for hold in holds if hold.get("is_blocker"))
    parts = [f"OPEN_HOLDS total={total}", f"overdue={overdue}", f"blockers={blockers}"]
    for hold in holds:
        parts.append(
            f"- {hold['id']} route={hold.get('hold_route', '?')} scope={hold.get('scope', '?')} "
            f"latest={hold.get('latest_safe_resolution', '?')} blocker={str(bool(hold.get('is_blocker'))).lower()} "
            f"overdue={str(bool(hold.get('is_overdue'))).lower()} target={hold.get('target', '?')}"
        )
    return "\n".join(parts)


def _markdown_summary(holds: list[dict[str, object]]) -> str:
    if not holds:
        return "## Open HOLDs\n\n(없음)"
    lines = [
        "## Open HOLDs",
        "",
        "| ID | route | scope | latest-safe-resolution | blocker | overdue | target |",
        "|----|-------|-------|------------------------|---------|---------|--------|",
    ]
    for hold in holds:
        lines.append(
            "| {id} | {route} | {scope} | {latest} | {blocker} | {overdue} | {target} |".format(
                id=hold["id"],
                route=hold.get("hold_route", "?"),
                scope=hold.get("scope", "?"),
                latest=hold.get("latest_safe_resolution", "?"),
                blocker="yes" if hold.get("is_blocker") else "no",
                overdue="yes" if hold.get("is_overdue") else "no",
                target=hold.get("target", "?"),
            )
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel-dir", required=True)
    parser.add_argument("--current-episode", type=int, default=0)
    parser.add_argument("--format", choices={"line", "markdown", "json"}, default="line")
    parser.add_argument("--fail-on-overdue", action="store_true")
    parser.add_argument("--fail-on-blocker", action="store_true")
    args = parser.parse_args(argv[1:])

    novel_dir = Path(args.novel_dir)
    review_log = novel_dir / "summaries" / "review-log.md"
    if not review_log.exists():
        print("OPEN_HOLDS total=0")
        return 0

    holds = _parse_hold_sections(review_log.read_text(encoding="utf-8"))
    open_holds: list[dict[str, object]] = []
    for hold in holds:
        if hold.get("status", "open").lower() == "resolved":
            continue
        latest_episode = _resolution_episode(hold.get("latest_safe_resolution", ""))
        is_overdue = (
            args.current_episode > 0
            and latest_episode is not None
            and args.current_episode > latest_episode
        )
        open_holds.append(
            {
                **hold,
                "latest_episode": latest_episode,
                "is_overdue": is_overdue,
                "is_blocker": _is_blocker(hold),
            }
        )

    _append_event(
        novel_dir,
        "hold_check_result",
        current_episode=args.current_episode,
        open_count=len(open_holds),
        overdue_count=sum(1 for hold in open_holds if hold["is_overdue"]),
        blocker_count=sum(1 for hold in open_holds if hold["is_blocker"]),
    )

    if args.format == "json":
        print(json.dumps(open_holds, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(_markdown_summary(open_holds))
    else:
        print(_line_summary(open_holds))

    if args.fail_on_blocker and any(hold["is_blocker"] for hold in open_holds):
        return 2
    if args.fail_on_overdue and any(hold["is_overdue"] for hold in open_holds):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
