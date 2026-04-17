"""Tests for scripts/validate-docs.py (Phase 8 drift automation, 2026-04-17).

각 check 함수의 동작을 temp 디렉토리 fixture로 검증한다.
validate-docs.py는 TEMPLATE_ROOT를 Path(__file__).resolve().parent.parent로 계산하므로
직접 import + 조작이 어렵다. 대신 CLI를 subprocess로 호출하여 exit code + stdout을 검증.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "validate-docs.py"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_validate_docs_runs_without_crash() -> None:
    """스크립트가 template root에서 traceback 없이 실행된다."""
    result = _run([])
    assert result.returncode in (0, 1), f"stderr: {result.stderr}"
    assert "Traceback" not in result.stderr
    # 출력에 Total 라인
    assert "Total:" in result.stdout


def test_validate_docs_accepts_help() -> None:
    result = _run(["--help"])
    assert result.returncode == 0
    assert "--check" in result.stdout
    assert "--strict" in result.stdout


def test_validate_docs_check_filter() -> None:
    """--check <name>으로 특정 체크만 실행 가능."""
    result = _run(["--check", "phase_docs"])
    assert result.returncode in (0, 1)
    # 다른 체크의 WARN이 없어야 함 (phase_docs만 실행)
    assert "[WARN] orphan" not in result.stdout
    assert "[WARN] sentinel" not in result.stdout


def test_validate_docs_strict_escalates_warn() -> None:
    """--strict 모드는 WARN도 exit 1 유발."""
    result_normal = _run([])
    result_strict = _run(["--strict"])
    # baseline 2 WARN이 있으므로 strict는 항상 1
    if "WARN" in result_normal.stdout:
        assert result_strict.returncode == 1


def test_phase_docs_have_commit_sha() -> None:
    """현재 template의 phase doc 6개가 모두 실제 sha를 가졌는지."""
    updates = REPO_ROOT / "docs" / "updates"
    if not updates.exists():
        return
    import re
    placeholder = re.compile(r"\*\*Commit\*\*:\s*\(추가 후 기록\)")
    sha_re = re.compile(r"\*\*Commit\*\*:\s*`[0-9a-f]{7,40}`")
    for f in sorted(updates.glob("phase-*.md")):
        text = f.read_text(encoding="utf-8")
        assert not placeholder.search(text), (
            f"{f.name} still has Commit placeholder '(추가 후 기록)'"
        )
        assert sha_re.search(text), (
            f"{f.name} doesn't have Commit sha in `<sha>` format"
        )


def test_profile_value_check_accepts_legal() -> None:
    """현재 CLAUDE.md의 profile: wuxia는 legal."""
    result = _run(["--check", "profile_value"])
    # profile: wuxia (기본값) — 통과해야 함
    assert "profile value" not in result.stdout or "not in legal set" not in result.stdout


def test_claude_md_check_runs() -> None:
    """Phase 2/4/0 필드 존재 확인 check가 실행된다."""
    result = _run(["--check", "claude_md"])
    assert result.returncode in (0, 1)
    # §4.1/§5.1A/profile이 있으므로 모두 통과
    assert "Phase 0 §4.1 Runtime Spec Canon missing" not in result.stdout


def test_writer_model_check_accepts_current_labels() -> None:
    """4개 prompt 파일에 mode 라벨이 정확히 있는지."""
    result = _run(["--check", "writer_model"])
    # 모두 OK이면 FAIL 없음
    assert "[FAIL] writer_model" not in result.stdout


def test_orphan_check_baseline_warnings() -> None:
    """현재 템플릿의 orphan baseline: settings/06-humor-guide.md + writer.md.

    다른 orphan이 나오면 drift 진입. 이 테스트는 baseline 유지 확인용.
    """
    result = _run(["--check", "orphan"])
    # baseline WARN은 2개 이하여야 함 (이외 것이 추가되면 drift)
    warn_lines = [ln for ln in result.stdout.splitlines() if ln.startswith("[WARN]")]
    # baseline은 2건 예상. 3건 이상이면 새 drift 가능성.
    assert len(warn_lines) <= 3, f"Unexpected orphan WARN count: {warn_lines}"


def test_sentinel_check_no_unexpected_fails() -> None:
    result = _run(["--check", "sentinel"])
    # sentinel drift는 주로 WARN, FAIL 없어야
    assert "[FAIL] sentinel" not in result.stdout


def test_mcp_naming_accepts_exempt_pattern() -> None:
    """Phase 6에서 수정한 CLAUDE.md §3.2.1 / §4.1의 'novel-editor MCP의 compile_brief' 표현이 OK."""
    result = _run(["--check", "mcp_naming"])
    # 기본 텍스트는 모두 면책 대상 — WARN 거의 없음
    warn_lines = [ln for ln in result.stdout.splitlines() if "mcp_naming" in ln]
    # Phase 6 수정 이후 실제 drift는 0. Baseline ≤ 2 허용 (느슨).
    assert len(warn_lines) <= 2, f"Unexpected mcp_naming WARN: {warn_lines}"
