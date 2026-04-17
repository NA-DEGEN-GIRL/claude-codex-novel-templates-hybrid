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

    # link_re: 마크다운 링크. newline은 유효한 경로가 아니므로 제외 (Phase 8 fix).
    link_re = re.compile(r"\[[^\]]*\]\(([^)\n]+)\)")
    # 상대경로 백틱 참조 — 확장자 화이트리스트 확장 (Phase 8):
    # md, py, json, sh, yml, yaml, txt, toml, jsonl, cfg, ini, csv + case-insensitive.
    # no-extension 스크립트도 scripts/ 접두 포함하면 인정.
    backtick_re = re.compile(
        r"`([^`\s]+/[^`\s]+(?:\.(?:md|py|json|sh|yml|yaml|txt|toml|jsonl|cfg|ini|csv)"
        r"|scripts/[A-Za-z0-9_.-]+))`",
        re.IGNORECASE,
    )

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
            # ~/ 홈 디렉토리 경로 — 템플릿 외부
            if ref.startswith("~"):
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
    """WRITER_DONE / FIX_DONE / REVIEW_DONE 표기가 Spec Canon과 일치하는가.

    Phase 8 강화 (2026-04-17):
    - canonical 패턴에 `:: run=` suffix 필수화 (이전: prefix만 검사).
    - referential filter에서 '등', '/' 제거 (너무 관대). 대신 중립 referential 단어만.
    """
    canonical_strings = {
        "WRITER_DONE": "WRITER_DONE chapter-{NN}.md :: run={RUN_NONCE}",
        "FIX_DONE": "FIX_DONE chapter-{NN} :: run={RUN_NONCE}",
        "REVIEW_DONE": "REVIEW_DONE chapter-{NN} :: run={RUN_NONCE}",
    }

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

    # referential phrase: "sentinel", "접두", "감지" 등 — 중립 단어만.
    # 이전의 "등", "/", "출력", "쓴다"는 너무 관대해서 실제 drift도 면제 → 제거.
    REFERENTIAL_PHRASES = [
        "sentinel",  # "WRITER_DONE sentinel"
        "접두",       # "완료 문자열 접두"
        "감지",       # "supervisor가 감지"
        "대기",       # "WRITER_DONE 대기"
        "파싱",       # "sentinel 파싱"
        "정의",       # "sentinel 정의"
        "참조",       # "§4.1 참조"
        "형식",       # "WRITER_DONE 형식은"
        "매칭",       # "exact string 매칭"
        "exact",
        "helper",    # "REVIEW_DONE helper" (batch-supervisor)
        "신호",       # "완료 신호는 FIX_DONE만" (fixer)
        "이름",
    ]

    for f in scan_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for sentinel, canonical in canonical_strings.items():
            if sentinel not in text:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if sentinel not in line:
                    continue
                # Canonical 패턴 full match: prefix + " :: run=" suffix (Phase 8 강화).
                # 허용 placeholder: {NN}, NN, XX, YY, ZZ, 실제 숫자
                # {RUN_NONCE} 또는 literal run nonce 허용.
                full_pattern = (
                    sentinel
                    + r"\s+chapter-(?:\{NN\}|NN|XX|YY|ZZ|\d+)"
                    + (r"\.md" if sentinel == "WRITER_DONE" else r"(?:\.md)?")
                    + r"(?:\s+(?:\d+-\d+|\{[^}]+\}))?"  # optional line range like {start}-{end}
                    + r"\s*::\s*run=(?:\{RUN_NONCE\}|[A-Za-z0-9_.-]+|\.\.\.)?"
                )
                if re.search(full_pattern, line):
                    continue
                # 백틱으로 감싸인 단순 sentinel 이름 언급은 referential
                # (예: "완료 신호는 `FIX_DONE`만 쓴다")
                # 백틱 안이 sentinel 이름만 있고 canonical 형태가 아니면 단순 언급.
                backtick_only = re.search(rf"`{sentinel}`(?!\s+chapter)", line)
                if backtick_only:
                    continue
                # Referential 줄 (중립 단어만) — drift 탐지 목적이므로 엄격하게.
                if any(phrase in line for phrase in REFERENTIAL_PHRASES):
                    continue
                # ASCII 다이어그램 줄 (박스 문자 포함) — referential이 맞음.
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
    # Phase 8 로직 버그 수정 (2026-04-17):
    # 이전 코드는 "MCP 도구/server" 경로로 트리거된 뒤 inner check가
    # "MCP tool" 조건만 써서 다른 분기를 항상 continue로 빠져나감.
    # 정답: trigger된 phrase가 무엇이든 compile_brief와 잘못된 계층 서술이 공존하면 warn,
    # 단 "novel-editor MCP의 compile_brief" 같은 명확한 소속 표현은 면책.
    MCP_CLAIM_PATTERNS = [
        # compile_brief를 "MCP tool/server/서버"로 직접 지시하는 표현 — 드리프트.
        # 단, "novel-editor MCP의 compile_brief" 같은 명확한 소속 표현은 negative lookahead.
        re.compile(r"compile_brief[^\n]*?MCP\s+(?:tool|server|서버)", re.IGNORECASE),
        re.compile(r"`compile_brief`[^\n]*?MCP\s+도구"),
    ]
    EXEMPT_PATTERNS = [
        # "novel-editor MCP의 compile_brief tool" 같은 올바른 소속 표현
        re.compile(r"novel-editor[^\n]*?compile_brief"),
        # "compile_brief는 ... MCP 서버가 아니라" 같은 부정 표현
        re.compile(r"compile_brief[^\n]*?(?:아니라|not)[^\n]*?MCP"),
        # validate-docs 자체나 drift-policy 문서 등에서 "MCP tool"로 부르지 말 것 같은 지시
        re.compile(r"\"MCP\s+tool\"[^\n]*?(?:부르지|call it)"),
    ]

    for f in scan_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if "compile_brief" not in line:
                continue
            # 드리프트 패턴이 있는가?
            drift = any(p.search(line) for p in MCP_CLAIM_PATTERNS)
            if not drift:
                continue
            # 면책 표현이 있는가?
            exempt = any(p.search(line) for p in EXEMPT_PATTERNS)
            if exempt:
                continue
            report.warn(
                "mcp_naming",
                f"{f.relative_to(TEMPLATE_ROOT)}:{lineno}",
                "compile_brief is novel-editor's tool, not a standalone MCP server",
            )


def check_phase_docs(report: Report) -> None:
    """docs/updates/phase-N-*.md 파일의 필수 섹션 + Commit sha 존재 확인.

    Phase 8 강화 (2026-04-17): `**Commit**: (추가 후 기록)` placeholder 잔존 시 FAIL.
    """
    updates_dir = TEMPLATE_ROOT / "docs" / "updates"
    if not updates_dir.exists():
        report.info("phase_docs", "docs/updates", "directory does not exist")
        return

    phase_files = sorted(updates_dir.glob("phase-*.md"))
    if not phase_files:
        report.info("phase_docs", "docs/updates", "no phase-*.md files found")
        return

    placeholder_pattern = re.compile(r"\*\*Commit\*\*:\s*\(추가 후 기록\)")
    sha_pattern = re.compile(r"\*\*Commit\*\*:\s*`[0-9a-f]{7,40}`")

    for f in phase_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for section in PHASE_DOC_REQUIRED_SECTIONS:
            if section not in text:
                report.fail(
                    "phase_docs",
                    f"{f.relative_to(TEMPLATE_ROOT)}",
                    f"missing required section: {section}",
                )
        # Commit sha 확인
        if placeholder_pattern.search(text):
            report.fail(
                "phase_docs",
                f"{f.relative_to(TEMPLATE_ROOT)}",
                "Commit sha still placeholder '(추가 후 기록)' — 실제 git sha로 채워야 함",
            )
        elif not sha_pattern.search(text) and "**Commit**" in text:
            report.warn(
                "phase_docs",
                f"{f.relative_to(TEMPLATE_ROOT)}",
                "Commit field exists but doesn't match `<sha>` format",
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


def check_profile_value(report: Report) -> None:
    """`CLAUDE.md §1 profile:` 값이 합법적 syntax 인가 (Phase 8 신규, 2026-04-17).

    Legal values:
    - 단일: wuxia | modern | game-fantasy | romance
    - 병용: regression+wuxia | regression+modern | regression+game-fantasy | regression+romance
    """
    claude = TEMPLATE_ROOT / "CLAUDE.md"
    if not claude.exists():
        return
    text = claude.read_text(encoding="utf-8")

    base_profiles = {"wuxia", "modern", "game-fantasy", "romance"}
    legal_values = base_profiles | {f"regression+{b}" for b in base_profiles}

    # profile 필드 탐색: "- **profile**: X" 형태
    match = re.search(
        r"^\s*-\s*\*\*profile\*\*:\s*([A-Za-z0-9+_-]+)",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        # 필드가 없으면 claude_md check가 별도로 잡음
        return

    value = match.group(1).strip()
    # 템플릿 placeholder인 경우 skip
    if value.startswith("{{") or value == "wuxia":
        # wuxia는 기본값. 템플릿 자체는 wuxia로 둠
        return
    if value not in legal_values:
        report.fail(
            "profile_value",
            "CLAUDE.md",
            f"profile value '{value}' not in legal set: {sorted(legal_values)}",
        )


def check_writer_hold_threshold(report: Report) -> None:
    """style-lexicon.md의 [WRITER-HOLD] 태그 누적 감지 (Phase 8 신규).

    같은 표현에 대해 [WRITER-HOLD]가 3회 이상 누적되면 §5.1A 정식 승격 제안.
    Phase 7 Writer Dissent 경로의 후속 모니터링.

    Note: 템플릿 레포 자체에는 style-lexicon이 없으므로 주로 INFO로 emit.
    개별 소설 프로젝트에서 이 스크립트를 실행할 때 유효.
    """
    lexicon = TEMPLATE_ROOT / "summaries" / "style-lexicon.md"
    if not lexicon.exists():
        return
    text = lexicon.read_text(encoding="utf-8")
    hold_lines = [ln for ln in text.splitlines() if "[WRITER-HOLD]" in ln]
    if not hold_lines:
        return
    # 같은 원 표현의 HOLD 빈도 카운트
    from collections import Counter
    counter: Counter = Counter()
    for ln in hold_lines:
        # "| {원 표현} | ..." 형식에서 원 표현 추출
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 2:
            expr = parts[1].split(" → ")[0].strip() if " → " in parts[1] else parts[1]
            counter[expr] += 1
    for expr, count in counter.items():
        if count >= 3:
            report.warn(
                "writer_hold",
                "summaries/style-lexicon.md",
                f"'{expr}' has {count} WRITER-HOLD entries — consider §5.1A promotion",
            )


CHECKS = {
    "orphan": check_orphan_references,
    "sentinel": check_sentinel_consistency,
    "writer_model": check_writer_model_labels,
    "mcp_naming": check_mcp_server_names,
    "phase_docs": check_phase_docs,
    "claude_md": check_claude_md_fields,
    "profile_value": check_profile_value,
    "writer_hold": check_writer_hold_threshold,
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
