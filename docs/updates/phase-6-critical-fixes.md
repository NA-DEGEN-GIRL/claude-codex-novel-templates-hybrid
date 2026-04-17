# Phase 6: Critical Correctness Fixes

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

5-agent 리뷰에서 발견된 Tier 0~1 critical 결함을 즉시 수정. Phase 0-5에서 남은 버그/모순/drift:

1. **Phase doc commit sha placeholder 6개 미채움** → 롤백 명령이 문자 그대로 실행 불가
2. **compile_brief `_extract_relationship_turning_points` 버그가 골든에 frozen**: 첫 테이블 헤더를 전체 매칭에 잘못 적용 → 3열 헤더 위에 6열 데이터
3. **unified-reviewer.md L169 "every episode"** vs Phase 2 기본값 false 모순 → reviewer가 매 화 무조건 호출 오인 가능
4. **unified-reviewer B1 Style consistency에 면책 체크 없음** (B2에만 있음) → voice convergence 플래그가 면책 전에 걸림
5. **4개 체커의 면책 목록이 서로 다름** → 같은 표현이 한 체커는 면책/다른 체커는 감점
6. **narrative-fixer "Surgeon" 은유 잔존 + fix-spec 스키마 부재** → Writer 입력 포맷 불일관
7. **Patch Classes 매핑 일부만** → S2/S4/S5/A1-A3/R1-R4 등 사용자 추정 의존
8. **HYBRID-DESIGN.md에서 compile_brief를 독립 MCP로 오기술** (Phase 5는 CLAUDE.md만 수정)
9. **README.md §0 사전 준비가 §1/§2 뒤에 배치** → 번호 역전으로 신규 사용자 혼란
10. **compile_brief 추가 버그들**: OPEN HOLD 중복 출력, col_count escaped pipe 오류, separator regex 누수, promise-tracker schema 하드코딩
11. **validate-settings.py**: _safe_read 실패 후 _require가 duplicate FAIL 양산
12. **event-log.py**: `inf`/`nan` 값 JSON 비호환 문자 emit 위험
13. **_estimate_source_size**가 plot/arc-*.md 전부 누락

## Changes

### A. Phase doc commit sha 채움 (6 files)

| Phase | File | Commit sha |
|-------|------|-----------|
| 0 | `docs/updates/phase-0-cleanup.md` | `4a71d44` |
| 1 | `docs/updates/phase-1-hot-path.md` | `513c911` |
| 2 | `docs/updates/phase-2-voice-preservation.md` | `32c8ae9` |
| 3 | `docs/updates/phase-3-role-consolidation.md` | `247861a` |
| 4 | `docs/updates/phase-4-genre-profiles.md` | `e208f1c` |
| 5 | `docs/updates/phase-5-drift-automation.md` | `5998a1d` |

### B. `compile_brief.py` — `_extract_relationship_turning_points` 재설계

**Before**: 파일 전체의 첫 번째 table header+separator만 찾아서 모든 turning point row 위에 prepend. 6열 만남 로그 데이터 행이 3열 관계 매트릭스 헤더 아래 들어감.

**After**: 파일을 **table block 단위**로 parsing. 각 block은 `{header, separator, rows, col_count}`. turning keyword를 포함한 row는 **자기가 속한 block의 header+separator**와 함께 출력. 여러 block에서 매칭되면 각각 독립 테이블로 이어 붙임.

골든 재생성 결과 `### 관계 전환점` 섹션이 올바르게 `| 화 | A | B | 유형 | 맥락 | 결과 |` 6열 헤더 + 6열 데이터로 일치.

### C. `unified-reviewer.md` L169 — "every episode" flag-aware 재기술

**Before**:
```markdown
External AI review (review_episode MCP) is now called every episode.
```

**After** (요약):
```markdown
External AI review (review_episode MCP) is flag-governed — called only for
sources whose {source}_feedback flag in CLAUDE.md §1 is true. Phase 2 기본값에서는
proxy만 on, 나머지는 opt-in. 플래그 모두 false면 skip, 에러 아님.
```

Domain expertise 테이블에도 각 source에 "(기본 ON/OFF, opt-in)" 라벨 추가.

### D. `unified-reviewer.md` B1 Style consistency에 면책 체크 추가

**Before**: B1 column 내용이 "Strip speaker tags / voice convergence" flag로 직행.

**After**: "**Override check first (Phase 2/6 voice preservation)**" 블록이 공통 면책 5종을 먼저 검사하고 매칭 시 즉시 면책. 모두 미매칭일 때만 voice convergence 검사.

### E. 4개 체커의 면책 목록 **공통 5종 통일**

**Before** (체커별 상이):
- unified-reviewer: §5.1A / style-lexicon / §0.5 (3종)
- narrative-fixer: §5.1A / style-lexicon / §0.5 (3종)
- korean-naturalness: §5.1A / style-lexicon / §0.5 (3종)
- repetition-checker: §5.1A / style-lexicon / decision-log / 03-characters / 관계 정점 (다른 5종)

**After** (공통 5종):
1. `CLAUDE.md §5.1A Intentional Style Deviations`에 등록된 표현
2. `summaries/style-lexicon.md`의 채택 어휘 또는 `[WRITER-HOLD: 사유]` 태그
3. `settings/01-style-guide.md §0.5 허용 이탈 유형`의 장면 변주 (위기/전투/내면/환상/유머/관계 정점)
4. `summaries/decision-log.md`의 프로젝트 단위 의도적 일탈
5. `settings/03-characters.md` "대표 대사 2~3종" 캐릭터 시그니처

각 체커 파일에 "이 5종 목록은 다른 3개와 동일. 변경 시 4개 파일 동시 갱신" 주석 추가.

unified-reviewer의 Role 섹션과 B2 면책 순위 섹션 양쪽에 동일 목록 명시.

### F. `narrative-fixer.md` — Core Principle 재프레이밍 + fix-spec 스키마 명세

**Before**: `## Core Principle: Surgeon, Not Author` — 실제 수정자 시점 문장. "Anchor every edit", "Resist over-rewriting"이 모두 Writer 관점.

**After**:
- 제목 → `## Core Principle: Surgeon's Brief, Not Author's Draft`
- 상단에 "이 원칙들은 **fix-spec에 반영할 지시 설계 원칙**이다" 명시
- 각 bullet을 "fix-spec은 ~~한다"로 재작성 (지시 생성 시점)

추가로 Patch Classes 섹션에 **fix-spec 필수 필드 스키마** 추가:
```markdown
- patch_class: micro | local | rewrite
- strategy: S1 | ... (복수 가능)
- target: chapters/{arc}/chapter-{NN}.md
- diagnosis: (원문 인용)
- instruction: (Writer에게 전달할 최소 지시)
- anchor: (기존 text/settings 근거)
- preserve: (건드리면 안 되는 것)
```

### G. Patch Classes 매핑 확장

기존 6개 전략만 매핑 → **18개 전략 전부 분류**:

| Class | 추가된 전략 |
|-------|-----------|
| micro | E4 Causal Bridge (single line), S4 Foreshadowing single insertion, A1 Action Trigger, R1 Arc Bookend |
| local | S5 Repetition (scene-wide), E4 (multi-line), A2 Reasoning, A3 Reaction Anchor, R2 Arc Bridge, R4 Character Note |
| rewrite | S2 large, S4 multi-episode planting, R3 Arc Restructure |

"매핑 원칙" 섹션 추가: 같은 전략도 scope에 따라 class 달라진다.

### H. `HYBRID-DESIGN.md` — compile_brief 정확 표기

**Before**:
- L64: `compile_brief, novel-calc, novel-hanja, novel-naming용 shell wrapper를 두지 않는다` — 4개 MCP 서버로 나열
- L86 표: `compile_brief` 행이 calc/hanja/naming과 동렬

**After**:
- L64: `novel-calc, novel-hanja, novel-naming, novel-editor` 4개 서버 나열. `compile_brief`는 "`novel-editor` MCP 서버의 tool"로 별도 문단에 명시.
- L86 표: 각 도구 옆에 `(server 이름)` 괄호 표기. `compile_brief (novel-editor)` 등.

### I. `README.md` — §0 사전 준비 위치 정정

**Before**: 빠른 시작 섹션 구조가 `1 → 2 → 0 → 3 → 4 → 5 → 6`. §0이 §1/§2 뒤에 배치되어 신규 사용자가 역진.

**After**: `1 (사전 준비: MCP clone) → 2 (새 프로젝트 생성) → 3 (설정 채우기) → 4 (MCP 등록) → 5 (직접 사용) → 6 (Supervisor) → 7 (Writer/Review 세션)`. 모든 섹션 번호 정순.

### J. `scripts/validate-settings.py` — duplicate FAIL 방지

**Before**: `_safe_read`가 파일 없음 → 빈 문자열 반환 + failure 1건 기록. 그 다음 `_require` 루프가 모든 needle에 대해 "missing" FAIL 추가로 기록 → **파일 1개 누락당 ~5건 duplicate FAIL**.

**After**: 각 `_require` 루프 앞에 `if style_guide:` / `if characters:` / `if running_context:` 조건 추가. 빈 문자열이면 needle 검사 skip.

### K. `scripts/event-log.py` — inf/nan 거부

**Before**: `float("inf")`/`float("nan")` 성공 → `json.dumps`가 non-JSON `Infinity`/`NaN` emit → strict consumer(jq, BigQuery, Polars)에서 파싱 실패.

**After**: `math.isinf(f) or math.isnan(f)` 체크 후 원본 string으로 fallback.

### L. `compile_brief.py` — HOLD dedup, col_count, separator regex, _estimate_source_size

1. **HOLD dedup** (L634-662): `open_holds`의 HOLD id set를 만들어, `hold_warning_lines` 중 해당 id를 포함하는 줄은 필터링. 같은 HOLD-NNN이 brief에 두 번 나오지 않음.

2. **col_count 수정** (L606-612): 이전 `len([c for c in header.split("|") if c.strip()])`가 빈 컬럼을 collapse → 3열이 2열로 보고됨. 수정: `header.count("|") - 1`.

3. **Separator regex 강화**: 이전 `startswith("|----")` → 3-dash (`|---|`), alignment (`|:---:|`) 미감지. 수정: `re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")`.

4. **_estimate_source_size 확장**: fixed_paths 20 → **27개** (plot/master-outline, timeline, prologue, epilogue + settings/02, 07, 08 추가) + `plot/arc-*.md` 동적 glob. "원본 합계" 수치의 정확도 크게 향상.

### M. `compile_brief.py` — promise-tracker header-aware parsing

**Before**: `cols[4]=due, cols[5]=priority` 하드코딩. no-title-023처럼 5컬럼 다른 스키마 프로젝트에서 wrong column 참조.

**After**: 헤더 행을 먼저 parsing하여 컬럼명 → 인덱스 매핑 생성. `_find_col(["예정", "마감", ...])` fuzzy match. 헤더가 없으면 기존 하드코딩 fallback. 신구 스키마 양쪽 지원.

## Rollback

### 전체 Phase 6 롤백
```bash
git revert <phase-6-commit-sha>
```

### 부분 롤백

**Phase doc sha만 돌리기**:
```bash
for f in docs/updates/phase-{0,1,2,3,4,5}-*.md; do
  sed -i 's/\*\*Commit\*\*: `[0-9a-f]*`/\*\*Commit\*\*: (추가 후 기록)/' "$f"
done
```

**compile_brief 변경만 되돌리기**:
```bash
git checkout <pre-phase-6-sha> -- compile_brief.py tests/golden/brief-ep2.md
```

**체커 면책 목록 복원 (4개)**:
```bash
git checkout <pre-phase-6-sha> -- .claude/agents/unified-reviewer.md .claude/agents/narrative-fixer.md .claude/agents/korean-naturalness.md .claude/agents/repetition-checker.md
```

**README §0 위치 복원**: `git checkout <pre-phase-6-sha> -- README.md`

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. 전체 테스트
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed

# 2. Phase doc sha 채움 확인
grep -l "(추가 후 기록)" docs/updates/phase-*.md
# → 빈 결과 (모두 치환됨)

# 3. 관계 전환점 헤더/데이터 컬럼 수 일치
grep -A 3 "관계 전환점" tests/golden/brief-ep2.md
# → 헤더/구분선/데이터 모두 6컬럼 | | | | | | |

# 4. OPEN HOLD 단일 출력
grep -c "HOLD-001" tests/golden/brief-ep2.md
# → 1

# 5. unified-reviewer B1에 Override check
grep -q "Override check first (Phase 2/6" .claude/agents/unified-reviewer.md && echo OK

# 6. 4 체커 면책 5종 동일
for f in unified-reviewer narrative-fixer korean-naturalness repetition-checker; do
  grep -c "summaries/decision-log.md" .claude/agents/$f.md
done
# → 모두 ≥1

# 7. event-log inf/nan 거부
python3 scripts/event-log.py /tmp/test-$$ test v=inf 2>&1 | tail -1
# 기록된 v는 "inf" (string) — JSON strict 호환

# 8. validate-settings 중복 FAIL 없음
python3 scripts/validate-settings.py --novel-dir /tmp/nonexistent-$$ 2>&1 | wc -l
# → 3 (각 missing file 1건만, 중복 없음)
```

## Dependencies

**선행**: Phase 0-5 모두 완료. 이 phase는 그 위에 critical fixes를 얹음.

**후행**:
- Phase 7: Profile + WRITER-HOLD 런타임 경로 연결 (이 phase의 공통 5종 통일이 Phase 7 §5.1A seed 제공의 기반)
- Phase 8: validate-docs.py 자체 개선 (이 phase에서 발견한 false positive/negative 패턴 기반으로 check 강화)

## Known Issues / Follow-ups

1. **validate-docs.py가 HYBRID-DESIGN.md §C 수정을 여전히 "compile_brief MCP tool" 경고로 잡음** (WARN 1건 추가). 실제로는 "아니라"로 명시적 negation이라 false positive. Phase 8에서 검출 로직 개선 대상.
2. **`unified-reviewer.md` B2의 "정량 트리거 (3회 이상 연속)" 카운트 수단**은 여전히 미확보. compile_brief가 P3/P5/P10 히스토리를 제공하지 않음. Phase 7 또는 별도로 episode-log 태그 스키마 확장 필요.
3. **`narrative-fixer.md`의 S1-S6 전략 설명 본문은 여전히 행동 동사** ("Identify, Split, Relocate"). Core Principle 재프레이밍으로 "fix-spec 지시 설계"임을 명확히 했으나, 18개 전략 전체 재작성은 범위 외.
4. **promise-tracker header-aware parsing의 fuzzy match**는 한국어 키워드 기반. 영어 컬럼명("due date", "priority") 사용 프로젝트는 별도 추가 필요.
5. **README §0 재정렬**이 이전 블로그/외부 레퍼런스의 "§3 Native MCP 등록" 링크를 깬다. 이 문서가 public 공유되면 redirect 또는 section anchor 갱신 필요.
6. **Patch Classes 매핑 표**는 narrative-fixer.md 서두에만 있음. fix-spec 작성 시 실제 참조성을 높이려면 `.claude/commands/narrative-fix.md` 같은 진입점에도 summary 제공 검토.
7. **Phase doc 롤백 섹션의 `<pre-phase-N-sha>`** 표기가 여전히 일반적. 각 phase의 "선행 커밋"을 명시 (예: Phase 6의 pre-sha = 5998a1d = Phase 5 sha)하면 더 정확.

## References

- 원 리뷰 (5-agent): Phase 0-5 작업 후 병렬 검토 결과에서 선별
- 영향 파일: `compile_brief.py`, `tests/golden/brief-ep2.md`, `scripts/validate-settings.py`, `scripts/event-log.py`, `.claude/agents/unified-reviewer.md`, `.claude/agents/narrative-fixer.md`, `.claude/agents/korean-naturalness.md`, `.claude/agents/repetition-checker.md`, `README.md`, `HYBRID-DESIGN.md`, `docs/updates/phase-{0,1,2,3,4,5}-*.md`
