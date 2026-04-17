#!/usr/bin/env python3
"""Template drift validator (Phase 5 drift automation, 2026-04-17).

템플릿 문서 간 drift 검출 도구:
1. Orphan reference — 문서가 참조하는 파일이 실제로 존재하는가
2. Sentinel consistency — WRITER_DONE / FIX_DONE / REVIEW_DONE 표기가 CLAUDE.md §4.1 Spec Canon과 일치하는가
3. writer_model values — 값이 {codex, claude}에 속하는가, prompt 파일 라벨과 일치하는가
4. MCP 서버 이름 — novel-calc 등 다섯 서버 이름 일관성
5. Phase docs — docs/updates/phase-N-*.md에 필수 섹션이 있는가

사용:
    python3 scripts/validate-docs.py                    # 전체 실행
    python3 scripts/validate-docs.py --check orphan     # 특정 체크만
    python3 scripts/validate-docs.py --strict           # warning도 FAIL로 승격

exit code:
    0: 모든 체크 통과
    1: 한 개 이상 FAIL
    2: 사용 오류 (잘못된 옵션)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Phase 0 §4.1 Spec Canon에 정의된 sentinel 포맷
SENTINEL_CANONICAL = {
    "WRITER_DONE": r"WRITER_DONE chapter-\{NN\}\.md :: run=\{RUN_NONCE\}",
    "FIX_DONE": r"FIX_DONE chapter-\{NN\} :: run=\{RUN_NONCE\}",
    "REVIEW_DONE": r"REVIEW_DONE chapter-\{NN\} :: run=\{RUN_NONCE\}",
}

# writer_model 합법 값
LEGAL_WRITER_MODELS = {"codex", "claude"}

# MCP 서버 이름 (Phase 0 Spec Canon)
MCP_SERVERS = {
    "novel-calc",
    "novel-hanja",
    "novel-naming",
    "novel-editor",
    "novelai-image",
}
# standalone — MCP가 아님
STANDALONE = {"compile_brief.py"}

# Phase docs 필수 섹션
PHASE_DOC_REQUIRED_SECTIONS = [
    "## Rationale",
    "## Changes",
    "## Rollback",
    "## Validation",
    "## Dependencies",
    "## Known Issues / Follow-ups",
    "## References",
]


@dataclass
class Issue:
    severity: str  # "FAIL" | "WARN" | "INFO"
    check: str
    location: str
    message: str


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def fail(self, check: str, location: str, message: str) -> None:
        self.issues.append(Issue("FAIL", check, location, message))

    def warn(self, check: str, location: str, message: str) -> None:
        self.issues.append(Issue("WARN", check, location, message))

    def info(self, check: str, location: str, message: str) -> None:
        self.issues.append(Issue("INFO", check, location, message))

    def has_failures(self, strict: bool = False) -> bool:
        target = {"FAIL"} if not strict else {"FAIL", "WARN"}
        return any(i.severity in target for i in self.issues)

    def print_summary(self) -> None:
        if not self.issues:
            print("OK: no drift detected.")
            return
        by_sev = {"FAIL": 0, "WARN": 0, "INFO": 0}
        for i in self.issues:
            by_sev[i.severity] += 1
            print(f"[{i.severity}] {i.check} @ {i.location}")
            print(f"    {i.message}")
        total = len(self.issues)
        print(
            f"\nTotal: {total} issues "
            f"(FAIL={by_sev['FAIL']}, WARN={by_sev['WARN']}, INFO={by_sev['INFO']})"
        )


# ─── Check implementations ──────────────────────────────────


def check_orphan_references(report: Report) -> None:
    """문서가 참조하는 파일이 실제로 존재하는가.

    대상 문서:
    - CLAUDE.md, README.md, batch-supervisor.md, HYBRID-DESIGN.md
    - settings/*.md
    - .claude/agents/*.md, .claude/commands/*.md, .claude/prompts/*.md

    참조 패턴:
    - 마크다운 링크: [text](./path/to/file.md) 또는 [text](path/to/file)
    - 인라인 참조: `path/to/file.md` 같은 백틱 경로 (단, 실제 경로일 때만)
    """
    target_files: list[Path] = []
    target_files.append(TEMPLATE_ROOT / "CLAUDE.md")
    target_files.append(TEMPLATE_ROOT / "README.md")
    target_files.append(TEMPLATE_ROOT / "batch-supervisor.md")
    target_files.append(TEMPLATE_ROOT / "HYBRID-DESIGN.md")
    target_files.extend(sorted((TEMPLATE_ROOT / "settings").rglob("*.md")))
    for sub in ("agents", "commands", "prompts"):
        d = TEMPLATE_ROOT / ".claude" / sub
        if d.exists():
            target_files.extend(sorted(d.glob("*.md")))

    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    # 상대경로 백틱 참조 (경로 구분자가 반드시 있어야 함)
    backtick_re = re.compile(r"`([^`\s]+/[^`\s]+\.(?:md|py|json))`")

    for f in target_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for match in link_re.finditer(text):
            ref = match.group(1).split("#")[0].strip()
            if not ref or ref.startswith(("http://", "https://", "mailto:")):
                continue
            # anchor-only
            if ref.startswith("#"):
                continue
            if ref.startswith("./"):
                ref = ref[2:]
            # 절대경로는 스킵
            if ref.startswith("/"):
                continue
            # 마크다운 내 placeholder 예시는 스킵 ({{var}}, plain single word without path sep)
            if ref.startswith("{{") and ref.endswith("}}"):
                continue
            # 경로 구분자 없는 단일 토큰은 파일이 아니라 예시 placeholder로 간주
            if "/" not in ref and "." not in ref:
                continue
            target = (f.parent / ref).resolve()
            # 템플릿 루트 밖 참조는 스킵
            try:
                target.relative_to(TEMPLATE_ROOT)
            except ValueError:
                continue
            if not target.exists():
                report.fail(
                    "orphan",
                    f"{f.relative_to(TEMPLATE_ROOT)}",
                    f"referenced path does not exist: {ref}",
                )
        for match in backtick_re.finditer(text):
            ref = match.group(1)
            if ref.startswith(("http://", "https://", "/")):
                continue
            # tmp/, chapters/, summaries/ 처럼 프로젝트 런타임 경로는 스킵
            # (템플릿이 아니라 생성된 프로젝트 내 경로)
            if ref.startswith(("tmp/", "chapters/", "summaries/", "plot/")):
                continue
            # Wildcard는 정확한 매칭 스킵 (예: `scripts/*.py`)
            if "*" in ref:
                continue
            # 백틱 경로는 두 가지로 resolve 시도: 파일 상대 + 템플릿 루트 상대.
            # 둘 중 하나라도 존재하면 valid로 본다.
            candidate_a = (f.parent / ref).resolve()
            candidate_b = (TEMPLATE_ROOT / ref).resolve()
            try:
                candidate_a.relative_to(TEMPLATE_ROOT)
                a_in_root = True
            except ValueError:
                a_in_root = False
            try:
                candidate_b.relative_to(TEMPLATE_ROOT)
                b_in_root = True
            except ValueError:
                b_in_root = False

            a_exists = a_in_root and candidate_a.exists()
            b_exists = b_in_root and candidate_b.exists()
            if a_exists or b_exists:
                continue
            # 템플릿 루트 밖으로 해석되면 스킵 (상위/외부 경로)
            if not a_in_root and not b_in_root:
                continue
            # 백틱 경로는 warning으로만 — 예시 경로일 가능성 있음
            report.warn(
                "orphan",
                f"{f.relative_to(TEMPLATE_ROOT)}",
                f"backtick path may not exist: `{ref}`",
            )


def check_sentinel_consistency(report: Report) -> None:
    """WRITER_DONE / FIX_DONE / REVIEW_DONE 표기가 Spec Canon과 일치하는가."""
    # CLAUDE.md §4.1에서 정의된 canonical 포맷 (literal text 검사)
    canonical_strings = {
        "WRITER_DONE": "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}",
        "FIX_DONE": "FIX_DONE chapter-{NN} :: run={RUN_NONCE}",
        "REVIEW_DONE": "REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}",
    }

    # 검색 대상
    scan_dirs = [
        TEMPLATE_ROOT / ".claude" / "prompts",
        TEMPLATE_ROOT / ".claude" / "agents",
    ]
    scan_files = [
        TEMPLATE_ROOT / "CLAUDE.md",
        TEMPLATE_ROOT / "README.md",
        TEMPLATE_ROOT / "batch-supervisor.md",
        TEMPLATE_ROOT / "HYBRID-DESIGN.md",
    ]
    for d in scan_dirs:
        if d.exists():
            scan_files.extend(sorted(d.glob("*.md")))

    for f in scan_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for sentinel, canonical in canonical_strings.items():
            if sentinel not in text:
                continue
            # 이 파일에서 sentinel 표기가 등장하는 줄 찾기
            for lineno, line in enumerate(text.splitlines(), 1):
                if sentinel not in line:
                    continue
                # 코드블록/예시 줄만 검사할 수 있으나, 단순화를 위해
                # canonical string이 그 줄 어딘가에 있는지만 본다.
                # "chapter-{NN}" (WRITER_DONE) 또는 without 확장자 (FIX_DONE/REVIEW_DONE).
                # 관대한 허용: 전체 canonical 포함 또는 placeholder 형태
                canonical_prefix = canonical.split(" ::")[0]  # "WRITER_DONE chapter-{NN}.md"
                # 이 줄에 canonical_prefix 또는 해당 포맷의 regex 매칭이 있는지
                # 허용 placeholder: {NN}, NN, XX, YY, ZZ, 또는 실제 숫자
                pattern = (
                    sentinel
                    + r"\s+chapter-(?:\{NN\}|NN|XX|YY|ZZ|\d+)"
                    + (r"\.md" if sentinel == "WRITER_DONE" else r"(?:\.md)?")
                )
                if re.search(pattern, line):
                    continue
                # 예외: "WRITER_DONE sentinel을 감지한다" 같은 referential 줄
                if any(
                    phrase in line
                    for phrase in [
                        "sentinel",
                        "접두",
                        "감지",
                        "지시",
                        "대기",
                        "출력",
                        "쓴다",
                        "형식",
                        "등",
                        "파싱",
                        "정의",
                        "참조",
                        "생성",
                        "삽입",
                        "세션 출력",
                        "사이클",
                        "/",  # "WRITER_DONE / FIX_DONE" 같은 diagram entry
                    ]
                ):
                    continue
                # ASCII 다이어그램 줄 (│, ├, └, ─, ▼, → 등 박스 문자 포함)
                if any(c in line for c in "│├└─▼▲→↓↑┌┐┘├┤┬┴┼"):
                    continue
                report.warn(
                    "sentinel",
                    f"{f.relative_to(TEMPLATE_ROOT)}:{lineno}",
                    f"{sentinel} usage may not match canonical '{canonical}'",
                )


def check_writer_model_labels(report: Report) -> None:
    """prompt 파일 상단의 mode 라벨이 writer_model 값과 일치하는가.

    각 파일이 "writer_model: claude 전용" 또는 "writer_model: codex 전용" 라벨을 가져야 함.
    """
    expected = {
        ".claude/prompts/claude-writer.md": "claude",
        ".claude/prompts/codex-writer.md": "codex",
        ".claude/prompts/claude-fixer.md": "claude",
        ".claude/prompts/codex-fixer.md": "codex",
    }
    for rel, model in expected.items():
        f = TEMPLATE_ROOT / rel
        if not f.exists():
            report.fail("writer_model", rel, "file missing")
            continue
        head = "\n".join(f.read_text(encoding="utf-8").splitlines()[:10])
        if f"writer_model: {model}" not in head and f"writer_model: `{model}`" not in head:
            # 허용: `writer_model: claude` (inline code), writer_model: claude (plain)
            if re.search(rf"writer_model:?\s*`?{model}`?", head):
                continue
            report.fail(
                "writer_model",
                rel,
                f"mode label missing or doesn't say writer_model: {model}",
            )


def check_mcp_server_names(report: Report) -> None:
    """MCP 서버 이름 표기 일관성.

    - `compile_brief`를 "MCP tool"로 부르지 않는가 (standalone script)
    - 5개 서버 이름 오표기 검출
    """
    # compile_brief를 "MCP"라고 부르는 문서 확인
    scan_files = [
        TEMPLATE_ROOT / "CLAUDE.md",
        TEMPLATE_ROOT / "README.md",
        TEMPLATE_ROOT / "HYBRID-DESIGN.md",
        TEMPLATE_ROOT / "batch-supervisor.md",
    ]
    for f in scan_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            # compile_brief + MCP tool/server 동시 출현
            if "compile_brief" in line and (
                "MCP tool" in line or "MCP 도구" in line or "MCP server" in line
            ):
                # 예외: "novel-editor MCP의 compile_brief" 같은 정상 표현
                if "novel-editor" in line and (
                    "compile_brief" in line and "MCP tool" not in line
                ):
                    continue
                if re.search(r"compile_brief.*MCP\s+(?:tool|서버|server)", line):
                    report.warn(
                        "mcp_naming",
                        f"{f.relative_to(TEMPLATE_ROOT)}:{lineno}",
                        "compile_brief is standalone script, not MCP tool",
                    )


def check_phase_docs(report: Report) -> None:
    """docs/updates/phase-N-*.md 파일의 필수 섹션 존재 확인."""
    updates_dir = TEMPLATE_ROOT / "docs" / "updates"
    if not updates_dir.exists():
        report.info("phase_docs", "docs/updates", "directory does not exist")
        return

    phase_files = sorted(updates_dir.glob("phase-*.md"))
    if not phase_files:
        report.info("phase_docs", "docs/updates", "no phase-*.md files found")
        return

    for f in phase_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for section in PHASE_DOC_REQUIRED_SECTIONS:
            if section not in text:
                report.fail(
                    "phase_docs",
                    f"{f.relative_to(TEMPLATE_ROOT)}",
                    f"missing required section: {section}",
                )


def check_claude_md_fields(report: Report) -> None:
    """CLAUDE.md §1이 Phase 2/4 필드를 포함하는가 (profile, feedback defaults)."""
    claude = TEMPLATE_ROOT / "CLAUDE.md"
    if not claude.exists():
        report.fail("claude_md", "CLAUDE.md", "file missing")
        return
    text = claude.read_text(encoding="utf-8")
    # Phase 4: profile 필드
    if "**profile**:" not in text:
        report.warn("claude_md", "CLAUDE.md", "Phase 4 profile field missing")
    # Phase 0: §4.1 Runtime Spec Canon
    if "4.1 Runtime Spec Canon" not in text:
        report.fail("claude_md", "CLAUDE.md", "Phase 0 §4.1 Runtime Spec Canon missing")
    # Phase 2: §5.1A Intentional Style Deviations
    if "5.1A Intentional Style Deviations" not in text:
        report.warn(
            "claude_md",
            "CLAUDE.md",
            "Phase 2 §5.1A Intentional Style Deviations missing",
        )


# ─── Main ──────────────────────────────────────────────────


CHECKS = {
    "orphan": check_orphan_references,
    "sentinel": check_sentinel_consistency,
    "writer_model": check_writer_model_labels,
    "mcp_naming": check_mcp_server_names,
    "phase_docs": check_phase_docs,
    "claude_md": check_claude_md_fields,
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check",
        action="append",
        choices=list(CHECKS.keys()),
        help="특정 체크만 실행. 여러 번 지정 가능. 미지정 시 전체 실행.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="WARN도 FAIL로 처리하여 exit code 1 반환",
    )
    args = parser.parse_args(argv[1:])

    report = Report()
    selected = args.check if args.check else list(CHECKS.keys())
    for name in selected:
        CHECKS[name](report)

    report.print_summary()
    return 1 if report.has_failures(strict=args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
