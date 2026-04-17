# Phase 8: validate-docs Hardening

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

python-pro / error-detective agent가 Phase 5의 `scripts/validate-docs.py`에서 여러 논리 버그와 false negative를 지적:

1. **sentinel regex에 `:: run=` suffix 부재** (L253): `WRITER_DONE chapter-05.md (no run=)` 같은 실제 drift를 canonical로 오판.
2. **check_mcp_server_names 로직 버그** (L341): outer if가 "MCP tool|MCP 도구|MCP server" 중 하나로 트리거되지만 inner `continue`는 "MCP tool" 만 검사 → 다른 두 분기는 항상 skip. docstring의 "5개 서버 이름 오표기 검출"이 구현되지 않은 상태.
3. **backtick_re 확장자 whitelist 좁음** (L134): `md|py|json`만. `.sh`/`.yml`/`.toml`/no-extension 스크립트는 영구 skip.
4. **referential filter 과도하게 관대** (L272): `"등"`, `"/"` 가 면제 조건에 포함되어 실제 drift도 면제. `"WRITER_DONE 등 sentinel 변경 필요"` 같은 줄도 통과.
5. **link_re가 newline 포함 ref 처리 안 함** (L132): 멀티라인 링크가 깨진 경로 추출.
6. **phase doc commit sha placeholder 검증 없음**: `(추가 후 기록)` 텍스트가 그대로 남아도 탐지 안 됨.
7. **profile 값 validation 없음**: `profile: xyz-random` 같은 잘못된 값 탐지 불가.
8. **tests/test_validate_docs.py 부재**: 8종 check 모두 무테스트 → 리팩토링 시 silent regression 위험.

Phase 8은 이 버그들을 수정하고, Phase 7에서 언급된 WRITER-HOLD 누적 모니터링을 위한 새 check 추가.

## Changes

### A. orphan check — extension whitelist 확장 + newline 대응

**link_re** (L132):
```python
# Before: r"\[[^\]]*\]\(([^)]+)\)"   # newline 포함 가능 → 깨진 경로
# After:  r"\[[^\]]*\]\(([^)\n]+)\)"  # newline 제외
```

**backtick_re** (L134):
```python
# Before: r"`([^`\s]+/[^`\s]+\.(?:md|py|json))`"
# After:  `md|py|json|sh|yml|yaml|txt|toml|jsonl|cfg|ini|csv` + IGNORECASE
#         + no-extension path `scripts/[A-Za-z0-9_.-]+` 인정
```

**홈 디렉토리 경로 skip** (L181 근방): `~/...` 로 시작하는 참조는 템플릿 외부이므로 skip.

### B. sentinel check — canonical 패턴 강화

**Before**: prefix만 매칭 (`WRITER_DONE chapter-{NN}.md`). suffix `:: run=` 부재도 canonical로 인정.

**After**:
```python
full_pattern = (
    sentinel
    + r"\s+chapter-(?:\{NN\}|NN|XX|YY|ZZ|\d+)"
    + (r"\.md" if sentinel == "WRITER_DONE" else r"(?:\.md)?")
    + r"(?:\s+(?:\d+-\d+|\{[^}]+\}))?"       # optional line range
    + r"\s*::\s*run=(?:\{RUN_NONCE\}|[A-Za-z0-9_.-]+|\.\.\.)?"
)
```

**Referential filter 정리**:
- 제거: `"등"`, `"/"`, `"출력"`, `"쓴다"`, `"사이클"`, `"생성"`, `"삽입"`, `"세션 출력"` (과도 관대)
- 유지 + 추가: `"sentinel"`, `"접두"`, `"감지"`, `"대기"`, `"파싱"`, `"정의"`, `"참조"`, `"형식"`, `"매칭"`, `"exact"`, `"helper"`, `"신호"`, `"이름"`

**백틱 감싼 단순 이름** (`` `FIX_DONE` ``)은 referential로 면책.

### C. mcp_naming check — 로직 버그 수정

**Before**: outer if는 trigger 3개 중 하나로 발동되지만 inner check가 `"MCP tool" not in line`만 사용 → 다른 trigger 분기가 항상 `continue`.

**After**: 명시적 **drift pattern 2종** + **exempt pattern 3종**:
```python
MCP_CLAIM_PATTERNS = [
    re.compile(r"compile_brief[^\n]*?MCP\s+(?:tool|server|서버)", re.IGNORECASE),
    re.compile(r"`compile_brief`[^\n]*?MCP\s+도구"),
]
EXEMPT_PATTERNS = [
    re.compile(r"novel-editor[^\n]*?compile_brief"),          # "novel-editor MCP의 compile_brief"
    re.compile(r"compile_brief[^\n]*?(?:아니라|not)[^\n]*?MCP"),  # "compile_brief는 MCP 서버가 아니라"
    re.compile(r"\"MCP\s+tool\"[^\n]*?(?:부르지|call it)"),    # "MCP tool로 부르지 말 것"
]
```

### D. phase_docs check — Commit sha placeholder 탐지

**Before**: 필수 섹션 존재만 검증.

**After**:
```python
placeholder_pattern = re.compile(r"\*\*Commit\*\*:\s*\(추가 후 기록\)")
sha_pattern = re.compile(r"\*\*Commit\*\*:\s*`[0-9a-f]{7,40}`")
# placeholder 잔존 → FAIL / sha 포맷 부적합 → WARN
```

발견 즉시 Phase 6, 7의 sha를 채움 (`69b9b51`, `3b66c6e`).

### E. profile_value check (신규)

`CLAUDE.md §1 profile:` 값이 합법 syntax인지 검증:
```python
base_profiles = {"wuxia", "modern", "game-fantasy", "romance"}
legal_values = base_profiles | {f"regression+{b}" for b in base_profiles}
```

템플릿 기본값 `wuxia` 또는 `{{...}}` placeholder는 통과. 그 외 legal_values에 없으면 FAIL.

### F. writer_hold check (신규)

`summaries/style-lexicon.md`의 `[WRITER-HOLD]` 태그를 **원 표현별로 카운트**하여 3회 이상 누적 시 WARN + `§5.1A Intentional Style Deviations` 정식 승격 제안.

Phase 7 Writer Dissent 경로의 후속 모니터링. 템플릿 레포에는 style-lexicon이 없으므로 대개 INFO로 emit; 개별 소설 프로젝트에서 이 스크립트 실행 시 실효.

### G. `tests/test_validate_docs.py` 신규

11개 테스트 추가:
- 스크립트 crash 없이 실행
- `--help`, `--check`, `--strict` CLI 플래그 동작
- phase doc commit sha 확인 (placeholder 없음 검증)
- profile_value, claude_md, writer_model, sentinel, mcp_naming, orphan 각 check별 단위 테스트
- orphan baseline 카운트 (3건 이하 — drift 진입 감지)

`subprocess`로 스크립트 CLI 호출하여 검증 (TEMPLATE_ROOT 의존성 회피).

### H. `docs/drift-policy.md` 업데이트

- 6종 check 테이블 → 8종으로 확장 (profile_value / writer_hold 추가)
- 각 check별 FAIL/WARN 조건 및 Phase 8 변경 내용 기술

## Rollback

### 전체 Phase 8 롤백
```bash
git revert <phase-8-commit-sha>
```

### 부분 롤백

**validate-docs.py만 이전 버전으로**:
```bash
git checkout <pre-phase-8-sha> -- scripts/validate-docs.py
```

**tests/test_validate_docs.py 제거**:
```bash
rm tests/test_validate_docs.py
```

**drift-policy.md 복원**:
```bash
git checkout <pre-phase-8-sha> -- docs/drift-policy.md
```

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. 전체 테스트 통과 (29개 = 기존 18 + 신규 11)
python3 -m pytest tests/ 2>&1 | tail -3
# → 29 passed

# 2. validate-docs baseline
python3 scripts/validate-docs.py 2>&1 | tail -5
# → FAIL=0, WARN=2 (baseline)

# 3. 모든 check 개별 실행 가능
for c in orphan sentinel writer_model mcp_naming phase_docs claude_md profile_value writer_hold; do
    python3 scripts/validate-docs.py --check "$c" 2>&1 | grep "Total:" || echo "$c: missing Total line"
done

# 4. Commit sha 검증
grep -r "(추가 후 기록)" docs/updates/phase-*.md
# → 빈 결과 (Phase 6/7 포함 모두 sha 채워짐)

# 5. strict 모드 exit code
python3 scripts/validate-docs.py --strict; echo "exit: $?"
# → exit 1 (baseline 2 WARN이 FAIL로 승격)

# 6. 새 check 동작 확인
grep "profile_value\|writer_hold" scripts/validate-docs.py | head -3
# → CHECKS 딕셔너리에 등록 확인
```

## Dependencies

**선행**:
- Phase 5: validate-docs.py 자체 신설 + 초기 6종 check
- Phase 6: Phase doc sha 채우기 작업 (이 phase가 잡은 placeholder drift를 먼저 수정)
- Phase 7: WRITER-HOLD 경로 도입 (writer_hold check가 이 메커니즘을 모니터링)

**후행**: 없음. Phase 8은 drift 자동화 수렴 phase.

## Known Issues / Follow-ups

1. **mcp_naming의 MCP_CLAIM_PATTERNS가 여전히 regex 기반** — 맥락을 완전히 이해하지 못함. 예: "compile_brief는 novel-editor MCP의 server 역할" 같은 의역 표현은 drift로 잘못 감지 가능. 향후 LLM 기반 의미 판정 검토.
2. **writer_hold check는 template root의 style-lexicon만 검사** — 개별 소설 프로젝트에서 실행하려면 `--novel-dir` 같은 옵션 추가 필요. 현재는 템플릿 레포에서 실행 시 대개 no-op.
3. **`check_sentinel`이 모든 줄을 순회** — O(files × lines × sentinels × filters). 템플릿 성장 시 O(n²) 경향. 현재 규모(~80 파일)에선 무시 가능이나 프로파일링 가치 있음.
4. **CI hook 자동 설치 여전히 수동**: drift-policy.md에 sample만 제공. `.git/hooks/pre-commit` 자동 설치 스크립트는 별도 과제.
5. **profile_value check가 `{{placeholder}}`를 통과** — 템플릿 자체에는 유효하지만 실 프로젝트에서 placeholder 잔존 시 탐지 안 됨. 프로젝트별 추가 check 필요 여지.
6. **test_validate_docs가 subprocess 기반**이라 타이밍 의존. timeout=30 지정. CI 느린 환경에서 flaky 가능성.
7. **Phase 8 이후 추가 drift 발견 시 phase-9 or follow-up file** — update log 구조가 안정화되었으므로 새 phase 추가 용이.

## References

- 원 리뷰 (5-agent): python-pro 에이전트 L253 sentinel / L134 backtick / L341 mcp_naming / L272 referential
- 원 리뷰: error-detective "validate-docs 자체의 정확성" 섹션
- 영향 파일: `scripts/validate-docs.py`, `tests/test_validate_docs.py` (신규), `docs/drift-policy.md`, `docs/updates/phase-6-critical-fixes.md` (sha 채움), `docs/updates/phase-7-profile-runtime.md` (sha 채움)
