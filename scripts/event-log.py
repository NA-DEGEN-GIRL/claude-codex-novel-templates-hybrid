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

    bool / null / int / float (finite only) / string 순서로 시도.
    inf/nan은 JSON 표준 비호환이므로 string으로 fallback (Phase 6 fix, 2026-04-17).
    """
    import math

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
        f = float(value)
    except ValueError:
        return value
    # inf/-inf/nan은 json.dumps가 allow_nan=True로 emit하면 strict consumer가 거부.
    # 안전하게 string으로 보존.
    if math.isinf(f) or math.isnan(f):
        return value
    return f


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
