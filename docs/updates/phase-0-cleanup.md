# Phase 0: Cleanup & Reorganization

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

리뷰 결과 최상위 root 19개 `.md` 중 **9개가 설계 이력/패치/제안서**로 확인됨. 운영 문서와 같은 층위에 있어 신규 사용자가 "이 PATCH를 지금 해야 하나?"로 오독할 위험. 추가로 README가 31.9KB임에도 TL;DR/목차가 없고, MCP 서버 git clone 사전 지시가 빠져 있으며, `claude mcp add` 명령어가 누락되어 `writer_model: claude` 사용자가 실행 단계에서 막힘.

또한 review mode 기본값이 `unified-reviewer.md`에서 "every 5"로 되어 있지만 `settings/07-periodic.md`는 "7화 간격"으로 정의 — critical drift.

Phase 0는 **파이프라인 로직에 손대지 않는 안전 작업**으로 설계 — drift/장벽 해소만.

## Changes

### 1. 설계·이력 문서를 `docs/archive/`로 이동

9개 파일을 `git mv`로 이동 (git history 보존).

| From (root) | To |
|-------------|------|
| `IMPLEMENTATION-LOG.md` | `docs/archive/IMPLEMENTATION-LOG.md` |
| `PATCH-NATIVE-MCP-CLEANUP.md` | `docs/archive/PATCH-NATIVE-MCP-CLEANUP.md` |
| `PROXY_FEEDBACK_PATCH.md` | `docs/archive/PROXY_FEEDBACK_PATCH.md` |
| `CLAUDE_PATCH_CLEAR_CONTINUITY.md` | `docs/archive/CLAUDE_PATCH_CLEAR_CONTINUITY.md` |
| `hybrid-agent-review.md` | `docs/archive/hybrid-agent-review.md` |
| `hybrid-prompt-review.md` | `docs/archive/hybrid-prompt-review.md` |
| `mcp-ideas-hybrid-detailed.md` | `docs/archive/mcp-ideas-hybrid-detailed.md` |
| `style-flexibility-proposal.md` | `docs/archive/style-flexibility-proposal.md` |
| `why-checker-design.md` | `docs/archive/why-checker-design.md` |

**이유**: 이들은 모두 (a) 이미 적용 완료된 변경 로그, (b) 미구현 제안서, (c) 설계 리뷰 노트 중 하나. 현행 운영에서 참조되지 않음.

**주의**: `style-flexibility-proposal.md`는 Phase 2에서 정식 적용되며, 그 때 해당 phase 문서가 이 archive 파일을 참조한다.

### 2. `docs/updates/` 신설

모든 phase 변경을 이 디렉토리에 기록한다. 파일:
- `docs/updates/README.md` — 인덱스 + 롤백 전략
- `docs/updates/phase-0-cleanup.md` — 이 문서
- `docs/updates/phase-N-*.md` — 향후 phase별

### 3. `README.md` — TL;DR + 목차 + 3분할

**Before**: 31.9KB README 최상단에 바로 `AI 한국어 웹소설 집필을 위한 하이브리드 파이프라인` 문장이 오고, 목차 없이 650줄이 linear하게 이어짐. "먼저 볼 문서"는 13개 항목을 flat 리스트로 나열.

**After**:
- **TL;DR 블록** 신설: 4 bullet로 템플릿 핵심 + 첫 화 경로 3단계 + 모드 선택 + 정본 우선순위
- **목차** 추가: 주요 섹션 14개 링크
- **"먼저 볼 문서" 3분할**:
  - 🚀 Getting Started (5단계 순서, INIT-PROMPT 중심)
  - ⚙️ Operations (batch-supervisor 중심, writer 프롬프트는 튜닝 시만)
  - 📐 Design Rationale (HYBRID-DESIGN, archive, updates)

### 4. `README.md` — MCP 서버 clone 사전 지시

**Before**: §3 "Native MCP 등록/확인"에 `codex mcp add` 명령어만 있고, 서버 자체가 로컬에 존재해야 한다는 전제가 명시되지 않음. 첫 사용자가 `python3 /root/novel/mcp-novel-calc/calc_server.py`에서 `No such file` 에러.

**After**: `### 0. 사전 준비: MCP 서버 clone` 섹션 신설. 5개 서버 `git clone` 명령 + 의존성 설치 안내. standalone 사용 시 `config.json` 전제 주의.

### 5. `README.md` — `claude mcp add` 명령어 추가

**Before**: §3 말미에 "`claude mode`를 쓸 때도 같은 MCP 서버들을 Claude Code 쪽에 맞게 등록/확인해야 한다" 한 줄로 실제 명령어 부재.

**After**: Codex 명령어 블록 아래에 Claude Code용 동일 명령어 블록 병렬 추가 (`claude mcp add novel-calc -- python3 ...` × 4). `claude mcp list` 확인 명령 포함.

### 6. `CLAUDE.md` — §4.1 Runtime Spec Canon 블록 추가

**Before**: sentinel 표기, writer_model 값, review mode 이름, MCP vs standalone script 구분이 문서마다 drift. 예: WRITER_DONE sentinel의 `.md` 포함 여부가 문서별로 다름.

**After**: `CLAUDE.md` §4 Document Authority 직후에 §4.1 Runtime Spec Canon 블록 삽입. 4개 테이블:
- Sentinel strings (exact match): WRITER_DONE은 `.md` 포함, FIX_DONE/REVIEW_DONE은 미포함
- `writer_model` 값 (`codex`|`claude`) vs 모드 라벨 (`codex mode`|`claude mode`)
- Review mode tiers: continuity (every), standard (every 7, max 8), full (arc boundary)
- MCP servers vs standalone scripts (`compile_brief`는 script, "MCP tool"로 부르지 말 것)

규칙: 이 블록이 정본. 다른 문서에서 값 변경 시 여기 먼저 고쳐야 함.

### 7. `unified-reviewer.md` L22 — review mode 기본값 5 → 7

**Before**:
```markdown
| `standard` | Per settings/07-periodic.md trigger rule (default every 5, flexible up to 8) | ...
```

**After**:
```markdown
| `standard` | Per settings/07-periodic.md trigger rule (default every 7, max 8) | ...
```

**이유**: settings/07-periodic.md L47-48이 "기본 periodic standard 점검은 6~8화 단위로 실행한다. 기본값은 7화 간격"으로 정의 — unified-reviewer가 drift였음.

### 8. `MIGRATION-PROMPT.md` — lean → hybrid 용어 치환

**Before**: 파일 전반에 "lean 구조", "lean 골격", "lean 체계", "lean 명칭", "lean 대응", "lean 기준" 등 20+ 인스턴스. 템플릿 이름은 hybrid인데 마이그레이션 타겟이 "lean"으로 기술 → 독자 혼동.

**After**: 아래 패턴을 `replace_all`로 일괄 치환.

| Pattern | → |
|---------|---|
| `lean 구조` | `hybrid 구조` |
| `lean 골격` | `hybrid 골격` |
| `lean 체계` | `hybrid 체계` |
| `lean 명칭` | `hybrid 명칭` |
| `lean 대응` | `hybrid 대응` |
| `lean 기준` | `hybrid 기준` |
| `lean 운영 절차` | `hybrid 운영 절차` |
| `lean 마이그레이션` | `hybrid 마이그레이션` |
| `lean 필수 필드` | `hybrid 필수 필드` |
| `lean style-guide` | `hybrid style-guide` |
| `lean에서` | `hybrid에서` |
| `lean의 신규` | `hybrid의 신규` |
| `lean 템플릿에서` | `이 템플릿에서` |
| `lean과 일치` | `hybrid와 일치` |
| `lean CLAUDE.md` | `hybrid CLAUDE.md` |
| `old → lean` | `old → hybrid` |

**유지**: L32의 "hybrid 템플릿은 lean 시리즈와 `settings/` 공통 authoring 레이어를 공유하는 Writer/Supervisor 분리 구조다" — 이는 의도적 lean 시리즈 참조. 원문("hybrid 템플릿은 lean 아키텍처 위에 Writer/Supervisor 분리 레이어를 추가한 것이다")은 이 공유 구조를 더 명확히 하도록 재서술.

## Rollback

### 전체 Phase 0 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-0-commit-sha>
```

### 개별 파일 복원

**9개 archive 파일을 root로 복귀**:
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git mv docs/archive/IMPLEMENTATION-LOG.md .
git mv docs/archive/PATCH-NATIVE-MCP-CLEANUP.md .
git mv docs/archive/PROXY_FEEDBACK_PATCH.md .
git mv docs/archive/CLAUDE_PATCH_CLEAR_CONTINUITY.md .
git mv docs/archive/hybrid-agent-review.md .
git mv docs/archive/hybrid-prompt-review.md .
git mv docs/archive/mcp-ideas-hybrid-detailed.md .
git mv docs/archive/style-flexibility-proposal.md .
git mv docs/archive/why-checker-design.md .
rmdir docs/archive  # 비어 있을 때만
```

**README TL;DR / 목차 제거**: `git checkout <pre-phase-0-sha> -- README.md`

**CLAUDE.md §4.1 Spec Canon 블록 제거**: `git checkout <pre-phase-0-sha> -- CLAUDE.md`

**unified-reviewer 기본값 되돌리기**: `git checkout <pre-phase-0-sha> -- .claude/agents/unified-reviewer.md`

**MIGRATION-PROMPT.md 원상 복구**: `git checkout <pre-phase-0-sha> -- MIGRATION-PROMPT.md`

## Validation

```bash
# 1. 9개 archive 파일이 이동되었는지
ls docs/archive/ | wc -l   # → 9

# 2. root에 해당 파일이 없는지
ls IMPLEMENTATION-LOG.md 2>&1   # → No such file

# 3. README에 TL;DR/목차 존재
grep -q "^## TL;DR" README.md && echo OK
grep -q "^## 목차" README.md && echo OK

# 4. MCP clone 지시 존재
grep -q "mcp-novel-editor" README.md && echo OK
grep -q "claude mcp add novel-calc" README.md && echo OK

# 5. CLAUDE.md Spec Canon 블록 존재
grep -q "4.1 Runtime Spec Canon" CLAUDE.md && echo OK

# 6. unified-reviewer 기본값
grep "default every" .claude/agents/unified-reviewer.md
# → "default every 7, max 8"

# 7. MIGRATION-PROMPT lean 잔재 확인 (1건만 의도적)
grep -c "lean" MIGRATION-PROMPT.md
# → 1 (L32 "lean 시리즈" 의도적 참조)

# 8. docs/updates/ 구조
ls docs/updates/
# → README.md, phase-0-cleanup.md
```

## Dependencies

**선행**: 없음 (Phase 0는 모든 phase의 선행).

**후행**:
- Phase 1: README/CLAUDE.md 편집이 Phase 1의 writer prompt 수정에 전제됨 (Spec Canon에 sentinel 포맷 명시 → writer prompts에서 참조)
- Phase 2: `docs/archive/style-flexibility-proposal.md`를 참조하여 정식 적용
- Phase 5: `docs/updates/` 구조가 drift 자동화 스크립트의 검증 대상이 됨

## Known Issues / Follow-ups

1. **README 여전히 큼** (~32KB): Phase 0는 구조만 정리. 상세 다이어그램/예시 축소는 범위 외.
2. **MIGRATION-PROMPT 상세 매핑표**는 여전히 old → hybrid로 기재되어 있으나 "old 템플릿"의 실제 모습 정의가 문서 내 없음. Phase 5 drift 자동화 시 후속 검토.
3. **batch-supervisor.md 47.8KB**는 여전히 목차 없음. Phase 1 또는 Phase 3에서 재검토.
4. **`IMPLEMENTATION-LOG.md`가 존재하지 않는 `IMPROVEMENT-REPORT-V2.md`를 참조**. archive로 옮겼지만 깨진 링크는 그대로. archive 내 문서 정리는 별도 작업.
5. **`.claude/prompts/archive/codex-writer-heavy.md`**는 이미 `.claude/prompts/archive/`에 있어서 root 정리와 별개. 유지.

## References

- 원 리뷰: `/root/novel/` 작업 세션의 Agent-based audit (2026-04-17)
- 영향 파일: `docs/archive/*` (9), `docs/updates/*`, `README.md`, `CLAUDE.md`, `.claude/agents/unified-reviewer.md`, `MIGRATION-PROMPT.md`
