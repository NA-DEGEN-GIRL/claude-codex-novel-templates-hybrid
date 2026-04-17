# Phase 5: Drift Automation

**Status**: ✅ Completed
**Commit**: `5998a1d`

## Rationale

Phase 0~4를 통해 템플릿의 drift 지점들이 다수 해결되었고 Spec Canon이 `CLAUDE.md §4.1`에 정의되었다. 하지만:

- **drift는 시간이 지나면 다시 쌓인다**: 새 기여자가 CLAUDE.md를 안 읽고 sentinel 이름을 쓰거나, profile 파일을 복사만 하고 필드 누락.
- **사람 review만으로는 한계**: 19개 문서 + 30+ 에이전트 간 일관성을 수동 확인 불가.
- **drift는 조용히 실패한다**: supervisor가 sentinel 매칭 실패할 때까지 발견 안 됨.

Phase 5는 **정적 문서 drift 자동 검증**을 추가한다. 6종 체크(orphan reference, sentinel consistency, writer_model labels, MCP naming, phase docs, CLAUDE.md fields)를 커맨드라인에서 실행 가능하며, CI hook으로 연결 가능.

## Changes

### 1. `scripts/validate-docs.py` 신설

413줄 Python 스크립트. 6개 check 구현:

| Check | 검증 내용 | 주요 탐지 사례 |
|-------|---------|--------------|
| `orphan` | 마크다운 링크/백틱 경로가 실제 파일과 일치 | 삭제된 파일 참조, 오타 경로, dead link |
| `sentinel` | WRITER_DONE/FIX_DONE/REVIEW_DONE 표기 | canonical format `chapter-{NN}.md :: run={RUN_NONCE}`과 불일치 |
| `writer_model` | prompt 파일의 mode 라벨 | `claude-writer.md`에 `writer_model: claude` 명시 누락 |
| `mcp_naming` | MCP 서버 vs standalone script 구분 | `compile_brief`를 "MCP 서버"로 오기술 |
| `phase_docs` | phase-N-*.md 필수 섹션 | Rationale/Changes/Rollback/Validation/Dependencies/Known Issues/References 누락 |
| `claude_md` | CLAUDE.md 필수 블록 | §4.1 Spec Canon, §5.1A Style Deviations, §1 profile 필드 |

**설계 원칙**:
- **False positive 최소화**: 마크다운 placeholder(`{{var}}`), ASCII 다이어그램(박스 문자), 단일 토큰 참조는 자동 스킵.
- **Exit code 분리**: 0=OK / 1=FAIL / 2=usage error. CI에서 활용 가능.
- **--strict 옵션**: WARN도 FAIL로 승격. 점진 도입 가능 (처음엔 느슨, 나중에 엄격).
- **개별 체크 실행**: `--check orphan` 등 선택 실행 — 대규모 문서 개편 시 부분 검증.

### 2. `docs/drift-policy.md` 신설

Drift 관리 정책 문서. 내용:
- 자동 검증 체크 6종 개요
- 사용법 (`python3 scripts/validate-docs.py --check ...`)
- **예상 baseline 경고 2건** 명시:
  1. `settings/06-humor-guide.md` (optional, 미배포)
  2. `.claude/agents/writer.md` 참조 in HYBRID-DESIGN.md (삭제된 파일의 historical context)
- **CI 통합 가이드**: git pre-commit hook + GitHub Actions workflow 샘플
- **정본 변경 절차**: Spec Canon 수정 시 순서(§4.1 먼저 → 다른 문서 → phase doc)
- **새 체크 추가 방법**
- **알려진 한계 4가지**

### 3. CLAUDE.md mcp_naming 불일치 수정

validate-docs 실행 결과 CLAUDE.md §3.2.1과 §4.1에 drift 발견:

**Before (§3.2.1 L98)**:
```markdown
1. **Call `compile_brief` MCP tool**: Generates...
```
— compile_brief를 "MCP tool"로 부름.

**Before (§4.1)**:
```markdown
- `compile_brief`는 **helper script**. "MCP tool"로 부르지 말 것.
```
— 정본이 "helper script"라고 명시, "MCP tool"로 부르지 말라고 지시.

두 문구가 서로 모순. 실제 구현은 **`compile_brief.py`는 스크립트이지만 `novel-editor` MCP 서버가 tool로 노출함**.

**After (§3.2.1)**:
```markdown
1. **Call `compile_brief` via `novel-editor` MCP server**: Generates... `compile_brief`는 이 템플릿에 포함된 Python 스크립트(`compile_brief.py`)를 `novel-editor` MCP 서버가 tool로 노출한다.
```

**After (§4.1)**:
```markdown
- **Template-bundled script exposed via MCP**: `compile_brief.py`는 이 템플릿에 포함된 스크립트이며, `novel-editor` MCP 서버가 이를 `compile_brief` tool로 노출한다. 호출 시 "via `novel-editor` MCP" 또는 "`compile_brief` tool" 표기 권장. "MCP 서버 이름"으로 오인하지 말 것.
```

Standalone scripts 목록도 template-bundled로 재분류하여 정확도 향상.

## Rollback

### 전체 Phase 5 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-5-commit-sha>
```

### 부분 롤백

**validate-docs.py 제거**:
```bash
rm scripts/validate-docs.py
rm docs/drift-policy.md
```
CLAUDE.md §3.2.1과 §4.1 mcp_naming 수정은 독립적이므로 유지해도 됨.

**CLAUDE.md mcp_naming 복원**: `git checkout <pre-phase-5-sha> -- CLAUDE.md`

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. validate-docs 실행 (baseline 2건 WARN, FAIL 0)
python3 scripts/validate-docs.py 2>&1 | tail -5
# → Total: 2 issues (FAIL=0, WARN=2, INFO=0)
# baseline: settings/06-humor-guide.md (optional), .claude/agents/writer.md (삭제됨)

# 2. 개별 체크 실행
python3 scripts/validate-docs.py --check phase_docs
# → 5개 phase docs 모두 필수 섹션 완비

python3 scripts/validate-docs.py --check writer_model
# → 4개 prompt 파일 모두 라벨 OK

python3 scripts/validate-docs.py --check claude_md
# → Phase 0/2/4 필드 모두 존재

# 3. drift-policy 존재
test -f docs/drift-policy.md && echo OK

# 4. 테스트 여전히 통과
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed

# 5. --strict mode에서의 baseline
python3 scripts/validate-docs.py --strict 2>&1 | tail -3
# → exit 1 (2 WARN을 FAIL로 승격). 이는 예상된 동작이며, pre-commit hook에서는 strict 비활성화 권장.
```

## Dependencies

**선행**:
- Phase 0 ~ 4: 모두 완료. validate-docs가 검증할 규칙들이 이들 phase에서 정립됨.
  - Phase 0: Spec Canon (sentinel format, writer_model values)
  - Phase 1: writer prompt 구조
  - Phase 2: §5.1A, feedback defaults
  - Phase 3: writer_model labels
  - Phase 4: profile field

**후행**: 없음 (Phase 5는 최종 phase).

향후 개선은 이 phase의 known issues 참조.

## Known Issues / Follow-ups

1. **CI hook 자동 설치 안 함**: `docs/drift-policy.md`에 pre-commit hook 샘플을 제공하지만, 자동 설치 스크립트는 없음. 사용자가 수동으로 `.git/hooks/pre-commit`에 복사해야 함. 이유: template 사용자의 기존 hook을 덮어쓸 위험 회피.
2. **GitHub Actions 미제공**: `.github/workflows/drift-check.yml` 파일을 템플릿에 포함하지 않음. 이유: 사용자별 workflow 설정 상이. 샘플만 docs/drift-policy.md에 제공.
3. **sentinel referential 필터의 false negative 위험**: "sentinel", "출력", "감지" 등의 단어가 포함되면 referential로 간주하여 검사 스킵. 실제 drift도 이들 단어와 같은 줄에 있으면 놓칠 수 있음. 경험적으로 Tune 필요.
4. **orphan check의 baseline 2건**: 의도적이지만 가시성 낮음. `.drift-ignore` 파일로 exclude 지정 가능하게 개선 여지.
5. **dynamic profile branching은 여전히 미구현**: Phase 4에서 profile 정적 문서만 추가. compile_brief.py의 profile-aware 분기는 별도 phase 필요. validate-docs에서 "CLAUDE.md profile 값이 settings/04-worldbuilding.md의 era와 일치하는가" 체크 추가는 향후 가능.
6. **한국어 문장 검증 없음**: validate-docs는 파일 참조/포맷 검증만 하고, 실제 문장의 모순(예: "기본값 7화"와 "기본값 5화"가 다른 줄에서 충돌)은 찾지 못함. 이는 LLM 기반 리뷰로만 가능.
7. **Performance**: 템플릿이 커지면 O(files × patterns) 스캔이 느려질 수 있음. 현재 크기(~80 파일)에서는 <1초로 무시 가능.

## References

- 원 리뷰: documentation-expert의 "drift가 예견된다" + Cross-reference audit의 orphan/definition conflict 지적
- 영향 파일: `scripts/validate-docs.py` (신규), `docs/drift-policy.md` (신규), `CLAUDE.md` §3.2.1 / §4.1 수정
