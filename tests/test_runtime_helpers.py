from __future__ import annotations

import json
import os
import shlex
import subprocess
import textwrap
import time
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
    )


def _events(novel_dir: Path) -> list[dict]:
    event_path = novel_dir / "tmp" / "run-metadata" / "events.jsonl"
    if not event_path.exists():
        return []
    rows = []
    for line in event_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _session_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _tmux_new_session(
    session: str,
    shell_snippet: str,
    *,
    env: dict[str, str] | None = None,
) -> None:
    result = _run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            session,
            f"bash -c {shlex.quote(shell_snippet)}",
        ],
        env=env,
    )
    if result.returncode != 0 and "Operation not permitted" in result.stderr:
        pytest.skip("tmux socket is unavailable in the current sandbox")
    assert result.returncode == 0, result.stdout + result.stderr
    time.sleep(1)


def _tmux_kill_session(
    session: str,
    *,
    env: dict[str, str] | None = None,
) -> None:
    _run(["tmux", "kill-session", "-t", session], env=env)


def test_tmux_send_claude_logs_runtime_events(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    tmux_dir = tmp_path / "tmux-claude"
    tmux_dir.mkdir(parents=True, exist_ok=True)
    session = _session_name("claude_helper")
    env = os.environ | {
        "NOVEL_EVENT_DIR": str(novel_dir),
        "TMUX_TMPDIR": str(tmux_dir),
    }
    shell_snippet = (
        "printf '❯ '; "
        "while IFS= read -r line; do "
        "printf '\\r\\033[K● Working\\n❯ '; "
        "done"
    )

    try:
        _tmux_new_session(session, shell_snippet, env=env)
        result = _run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "tmux-send-claude"),
                session,
                "single line test",
                "1",
                "80",
            ],
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "CLAUDE_RESPONSE_CONFIRMED" in result.stdout

        events = _events(novel_dir)
        assert any(event["event"] == "tmux_send_claude_start" for event in events)
        assert any(
            event["event"] == "tmux_send_claude_result"
            and event["status"] == "CLAUDE_RESPONSE_CONFIRMED"
            for event in events
        )
    finally:
        _tmux_kill_session(session, env=env)


def test_tmux_send_codex_logs_runtime_events(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    tmux_dir = tmp_path / "tmux-codex"
    tmux_dir.mkdir(parents=True, exist_ok=True)
    session = _session_name("codex_helper")
    env = os.environ | {
        "NOVEL_EVENT_DIR": str(novel_dir),
        "TMUX_TMPDIR": str(tmux_dir),
    }
    shell_snippet = (
        "printf '› '; "
        "while IFS= read -r line; do "
        "printf '\\r\\033[KWorking\\n› '; "
        "done"
    )

    try:
        _tmux_new_session(session, shell_snippet, env=env)
        result = _run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "tmux-send-codex"),
                session,
                "single line test",
                "1",
                "80",
            ],
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "WORKING_CONFIRMED" in result.stdout

        events = _events(novel_dir)
        assert any(event["event"] == "tmux_send_codex_start" for event in events)
        assert any(
            event["event"] == "tmux_send_codex_result"
            and event["status"] == "WORKING_CONFIRMED"
            for event in events
        )
    finally:
        _tmux_kill_session(session, env=env)


def test_tmux_wait_sentinel_file_fallback_logs_event(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    tmux_dir = tmp_path / "tmux-sentinel"
    tmux_dir.mkdir(parents=True, exist_ok=True)
    session = _session_name("sentinel_helper")
    env = os.environ | {
        "NOVEL_EVENT_DIR": str(novel_dir),
        "TMUX_TMPDIR": str(tmux_dir),
    }
    sentinel = "WRITER_DONE chapter-05.md :: run=test-1234"
    sentinel_file = novel_dir / "tmp" / "sentinels" / "chapter-05.done"

    try:
        _tmux_new_session(session, "exec bash", env=env)
        proc = subprocess.Popen(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "tmux-wait-sentinel"),
                session,
                sentinel,
                "5",
                "1",
                "50",
                "0",
                str(sentinel_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        time.sleep(1)
        sentinel_file.parent.mkdir(parents=True, exist_ok=True)
        sentinel_file.write_text(sentinel + "\n", encoding="utf-8")
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 0, stdout + stderr
        assert "mode=file_fallback" in stdout

        events = _events(novel_dir)
        assert any(event["event"] == "tmux_wait_sentinel_start" for event in events)
        assert any(
            event["event"] == "tmux_wait_sentinel_result"
            and event["status"] == "SENTINEL_FOUND"
            and event.get("mode") == "file_fallback"
            for event in events
        )
    finally:
        _tmux_kill_session(session, env=env)


def test_check_open_holds_reports_overdue_and_blocker(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    _write(
        novel_dir / "summaries" / "review-log.md",
        """
        ### HOLD-001
        - hold_route: forward-fix
        - scope: current-arc
        - issue: 감정 근거 부족
        - target: 4화 보상
        - latest-safe-resolution: 3화
        - status: open
        - blocker: no

        ### HOLD-002
        - hold_route: plot-repair
        - scope: current-arc
        - issue: 플롯 동선 충돌
        - target: 5화 전 수정
        - latest-safe-resolution: 5화
        - status: open
        - blocker: yes
        """,
    )

    overdue = _run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "check-open-holds.py"),
            "--novel-dir",
            str(novel_dir),
            "--current-episode",
            "4",
            "--fail-on-overdue",
        ]
    )
    assert overdue.returncode == 1, overdue.stdout + overdue.stderr
    assert "HOLD-001" in overdue.stdout
    assert "overdue=true" in overdue.stdout

    blocker = _run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "check-open-holds.py"),
            "--novel-dir",
            str(novel_dir),
            "--current-episode",
            "4",
            "--fail-on-blocker",
        ]
    )
    assert blocker.returncode == 2, blocker.stdout + blocker.stderr
    assert "HOLD-002" in blocker.stdout
    assert "blocker=true" in blocker.stdout


def test_summarize_runtime_metrics_reports_key_counts(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    event_path = novel_dir / "tmp" / "run-metadata" / "events.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"ts": "2026-04-11T00:00:00Z", "event": "read_missing"},
        {"ts": "2026-04-11T00:00:01Z", "event": "read_error"},
        {"ts": "2026-04-11T00:00:02Z", "event": "review_done_gate_failed"},
        {"ts": "2026-04-11T00:00:03Z", "event": "hold_check_result"},
        {
            "ts": "2026-04-11T00:00:04Z",
            "event": "tmux_send_codex_result",
            "status": "WORKING_CONFIRMED",
        },
        {
            "ts": "2026-04-11T00:00:05Z",
            "event": "tmux_wait_sentinel_result",
            "status": "SENTINEL_FOUND",
        },
        {
            "ts": "2026-04-11T00:00:06Z",
            "event": "compile_brief_complete",
            "size_bytes": 1200,
        },
        {
            "ts": "2026-04-11T00:00:07Z",
            "event": "compile_brief_complete",
            "size_bytes": 800,
        },
    ]
    event_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = _run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "summarize-runtime-metrics.py"),
            "--novel-dir",
            str(novel_dir),
            "--format",
            "json",
        ]
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["total_events"] == 8
    assert payload["read_missing"] == 1
    assert payload["read_error"] == 1
    assert payload["review_gate_failed"] == 1
    assert payload["hold_checks"] == 1
    assert payload["brief_runs"] == 2
    assert payload["avg_brief_size_bytes"] == 1000
    assert payload["send_result_counts"]["WORKING_CONFIRMED"] == 1
    assert payload["wait_result_counts"]["SENTINEL_FOUND"] == 1


def test_suggest_voice_profile_refresh_returns_candidates(tmp_path: Path) -> None:
    novel_dir = tmp_path / "novel"
    _write(
        novel_dir / "chapters" / "prologue" / "chapter-01.md",
        """
        # 1화 - 검은 봉투

        서린은 골목 가장자리에서 봉투의 모서리를 손톱으로 눌렀다. 종이 안쪽의 굳은 감촉이
        아직 살아 있다는 사실이 마음을 더 조급하게 만들었다. 뒤를 돌아보면 끝이라는 판단은
        두려움보다 먼저 몸을 움직이게 했고, 시장 사람들의 어깨 사이로 스며드는 걸음도 그 계산을
        따라 빨라졌다.

        "지금 멈추면 다 늦어."

        그는 그렇게 중얼거린 뒤에도 속도를 늦추지 않았다.

        ---
        ### EPISODE_META
        ```yaml
        characters_appeared:
          - 서린
        ```
        """,
    )

    result = _run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "suggest-voice-profile-refresh.py"),
            "--novel-dir",
            str(novel_dir),
            "--from-episode",
            "1",
            "--to-episode",
            "1",
            "--top",
            "1",
            "--format",
            "json",
        ]
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["chapter"] == "chapter-01.md"
    assert "봉투의 모서리" in payload[0]["text"]
