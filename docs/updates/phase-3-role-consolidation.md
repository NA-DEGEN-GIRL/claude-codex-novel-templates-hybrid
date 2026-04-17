# Phase 3: Role Consolidation

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

원 리뷰(prompt-engineer 에이전트)에서 지적된 세 가지 역할 혼란:

1. **narrative-fixer Role 이중성**: 상단은 "surgical rewrite specialist"로 자기 정의했으나 Hybrid Execution Note에서 "실제 수정은 Writer 세션"으로 뒤집힘. Claude supervisor가 "내가 수정하는 agent"로 오인할 위험 — hybrid pipeline 붕괴의 원인.
2. **narrative-fixer 18 전략의 과도한 분류 비용**: S1-S6 + E1-E4 + A1-A3 + R1-R4 + 기타 전략을 매번 선택하는 오버헤드가 실제 fix 비용(대부분 1~3 문장 삽입/교체)보다 큼.
3. **writer_model 분기 라벨 부재**: `claude-writer.md`/`codex-writer.md`에 "이 파일은 어느 mode 전용" 명시가 없어 supervisor 선택 실수 시 tmux 제어(Enter 타이밍, sentinel)가 어긋나 runtime 실패.

추가로 §5.12 (co-present characters)가 4곳에 분산되어 있어 한 곳만 수정 시 drift 위험.

## Changes

### 1. `.claude/agents/narrative-fixer.md` — Role 재정의

**Before** (L5-8):
```markdown
## Role

You are a **surgical rewrite specialist**. You change the minimum necessary...
```

이후 Hybrid Execution Note가 이 Role과 충돌.

**After**:
```markdown
## Role

You are a **fix-spec generator**, not a rewriter (Phase 3 role consolidation, 2026-04-17). You read a diagnosis, decide what minimum change resolves it, and produce a surgical fix-spec that the Writer session will execute. You never directly modify `chapters/*.md` — that is Writer's job.
```

그리고 **Responsibilities** + **What you do NOT do** 섹션 신설 — "직접 수정 안 함" + "metadata는 수정" 명확히 구분.

### 2. `.claude/agents/narrative-fixer.md` — Patch Classes 도입

18개 전략을 한 번에 고르는 비용을 줄이기 위해, 먼저 3단계 patch class로 분류:

| Class | Scope | Typical strategies | Post-fix verification |
|-------|-------|-------------------|----------------------|
| **micro** | 1~3 sentences | E1, E2, E3, small S5 | 에피소드 단위 1회 (batch) |
| **local** | 1~2 paragraphs | S2 small, S3 small, E4 | 에피소드 단위 1회 (batch) |
| **rewrite** | Scene or multi-scene | S1, S3 large, S4 multi-ep, S6 | item 단위 |

기존 18 전략은 **rewrite class에서 주로 참조**하는 상세 카탈로그로 유지. 대부분의 실제 fix는 micro + local.

### 3. `.claude/agents/narrative-fixer.md` — Step 3 rename

**Before**: `### Step 3: Execute (Hybrid: fix-spec → Writer 세션)`
**After**: `### Step 3: Generate fix-spec`

이름만으로 "supervisor가 직접 Execute하지 않음"을 명확히.

Batch 검증 최적화 추가: 같은 에피소드 내 micro/local fix 여러 건은 모두 적용 후 continuity 1회만 재검증. rewrite만 item 단위. fix-spec에 `patch_class` 필드 명시.

### 4. writer_model 분기 라벨 추가 (4 파일)

`.claude/prompts/claude-writer.md`, `codex-writer.md`, `claude-fixer.md`, `codex-fixer.md` 각각 상단에 모드 라벨 추가:

```markdown
> **🏷️ 모드 라벨 (Phase 3 role consolidation, 2026-04-17)**: 이 파일은 `writer_model: {claude|codex}` 전용. 다른 mode에는 `{반대 파일}`을 사용. supervisor가 잘못 선택하면 tmux 세션 제어 명령(Enter 타이밍, sentinel 매칭)이 어긋나 runtime 실패.
```

### 5. `settings/03-characters.md` — §5.12 pointer 추가

`장면 동석 인물 처리 원칙` 섹션 상단에 상위 규칙 참조 명시:

```markdown
> 상위 금지 규칙은 `CLAUDE.md §5.12 No invisible co-present characters`에 있다. 여기서는 그 규칙을 **어떻게 구현할지 운용 디테일**만 다룬다. (Phase 3 role consolidation — single source of truth for the prohibition is §5.12.)
```

**의도**: settings/03-characters.md가 "상세 구현 디테일"이고 CLAUDE.md §5.12가 "prohibition 정본"임을 명확화. 양쪽 모두 유지하되 계층 관계를 드러냄.

**§5.12가 등장하는 4곳**:
1. **`CLAUDE.md §5.12`** (source of truth, 수정 불필요)
2. **`settings/03-characters.md`** L9 — pointer 추가 (이번 phase)
3. **`.claude/prompts/claude-writer.md`, `codex-writer.md`** L37 "carry-forward 존중" — active drafting guidance. pointer보다 내재화 유지가 writer 품질에 유리. 유지.
4. **`.claude/agents/unified-reviewer.md` A #14 + `scene-logic-checker.md`** — detection/enforcement. 이미 "명백한 위반만" 좁혀져 있어 overlap 경감됨. 유지.

결론: **Single source of truth는 §5.12**, 다른 3곳은 계층 내 역할 분담(operational / active / detection). 완전 통합보다 계층 명시가 운영에 유리.

## Rollback

### 전체 Phase 3 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-3-commit-sha>
```

### 부분 롤백

**narrative-fixer Role만 복원**:
```bash
git checkout <pre-phase-3-sha> -- .claude/agents/narrative-fixer.md
```
> 주의: Phase 2에서 추가한 Override check 블록이 같은 파일에 있음. Phase 2 commit을 먼저 찾아서 cherry-pick 필요할 수 있음.

**writer_model 라벨만 제거**:
```bash
git checkout <pre-phase-3-sha> -- .claude/prompts/claude-writer.md .claude/prompts/codex-writer.md .claude/prompts/claude-fixer.md .claude/prompts/codex-fixer.md
```

**settings/03-characters.md pointer만 제거**: 파일에서 §5.12 pointer blockquote 삭제.

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. narrative-fixer Role 재정의 확인
grep -A2 "^## Role" .claude/agents/narrative-fixer.md | grep -q "fix-spec generator" && echo OK

# 2. Patch Classes 존재 확인
grep -q "## Patch Classes" .claude/agents/narrative-fixer.md && echo OK

# 3. Step 3 rename 확인
grep -q "### Step 3: Generate fix-spec" .claude/agents/narrative-fixer.md && echo OK

# 4. writer_model 라벨 4파일 확인
for f in .claude/prompts/claude-writer.md .claude/prompts/codex-writer.md .claude/prompts/claude-fixer.md .claude/prompts/codex-fixer.md; do
    grep -q "모드 라벨 (Phase 3 role consolidation" "$f" && echo "$f: OK"
done

# 5. settings/03-characters.md §5.12 pointer
grep -q "CLAUDE.md §5.12" settings/03-characters.md && echo OK

# 6. 테스트 통과
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed
```

## Dependencies

**선행**:
- Phase 0: Spec Canon (writer_model 값 정의)
- Phase 1: writer prompt diet (상단 위치 명확)
- Phase 2: Override check가 narrative-fixer Required Context에 이미 추가되어 있어, Phase 3의 Role 재정의 시 유지하기만 하면 됨

**후행**:
- Phase 4: 장르 프리셋에서 writer prompt 선택 로직이 writer_model 라벨을 근거로 검증 가능
- Phase 5: drift 자동화에서 "writer_model 값이 prompt 파일 라벨과 일치하는가" 검증 대상 포함

## Known Issues / Follow-ups

1. **18개 전략의 별도 파일 분리**는 이번 phase에서 **하지 않음**. 이유: strategies가 `--source oag`, `--source why-check`, `--source arc-read` 등 여러 flow에서 참조되며, 분리 시 경로 갱신이 많아짐. 대신 Patch Classes가 "대부분의 fix는 micro/local"을 시각적으로 명시해 "18개 중 하나를 매번 고른다"는 부담을 완화.
2. **`§5.12 single source of truth` 이상으로 통합하지 않음**. 4곳이 layered 역할이라 단순 통합이 오히려 writer/reviewer 양쪽 가이드를 약화. 명시적 pointer만 추가.
3. **narrative-fixer.md가 여전히 500+ 줄**. Phase 3 전략 카탈로그 분리는 후속 개선 여지. 현재는 관련 섹션에 "자주 사용 vs 드물게 사용" 표식만 간접 적용.
4. **patch_class 필드**는 fix-spec 파일 스키마에 추가됨. 기존 fix-spec 샘플/템플릿을 모두 갱신해야 하나, 이 phase에서 찾은 활성 샘플 없어 문서만 갱신. Writer/fixer 프롬프트는 `patch_class: micro, local, rewrite` 이미 명시됨.
5. **writer_model 라벨**이 단순 경고 문구. supervisor가 잘못된 prompt 파일을 선택해도 자동 감지하지 않음. Phase 5 drift 자동화에서 validate-docs.py가 supervisor 로그 vs 파일 라벨 교차 검증 추가 권장.

## References

- 원 리뷰: prompt-engineer 에이전트의 "narrative-fixer Role 이중성", "18개 전략 과분류", "writer_model 분기 라벨 부재" 지적
- 영향 파일: `.claude/agents/narrative-fixer.md`, `.claude/prompts/claude-writer.md`, `.claude/prompts/codex-writer.md`, `.claude/prompts/claude-fixer.md`, `.claude/prompts/codex-fixer.md`, `settings/03-characters.md`
