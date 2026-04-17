#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _usage() -> int:
    print(
        "Usage: event-log.py NOVEL_DIR EVENT_TYPE [key=value ...]",
        file=sys.stderr,
    )
    return 64


def _coerce(value: str):
    """payload 값을 JSON 호환 타입으로 변환.

    bool / null / int / float / string 순서로 시도.
    float 추가 (이전에는 float 값이 그대로 string이 되는 버그).
    """
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        return _usage()

    novel_dir = Path(argv[1])
    event_type = argv[2]
    payload = {}

    for item in argv[3:]:
        if "=" not in item:
            print(f"Invalid payload item: {item}", file=sys.stderr)
            return 64
        key, value = item.split("=", 1)
        payload[key] = _coerce(value)

    event_path = novel_dir / "tmp" / "run-metadata" / "events.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "event": event_type,
        **payload,
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    print(event_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
