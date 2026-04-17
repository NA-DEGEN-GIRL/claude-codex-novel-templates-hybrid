# Phase 1: Hot Path Optimization

**Status**: ✅ Completed
**Commit**: `513c911`

## Rationale

매 화 반복 실행되는 3개 경로가 이 템플릿의 load-bearing 부분.

1. **writer prompt 주입** (claude-writer.md / codex-writer.md): 활성 체크포인트 약 39개로 인지부하 과다 → 체크리스트 편향 발생, 서사 리듬 훼손
2. **compile_brief.py 출력**: 매 에피소드 LLM 입력용으로 생성되는데 테이블 포맷 깨짐 3건 + schema mislabel 1건 + 중복 출력 1건 → LLM이 컬럼 추론 실패, 토큰 10~15% 낭비
3. **supervisor 배치 안정성**: `validate-settings.py`가 파일 누락 시 traceback crash → supervisor hard-stop 위험

Phase 1는 이 세 경로만 타격 — 구조적 변경은 Phase 2 이후.

## Changes

### A. Writer prompt 다이어트

#### `.claude/prompts/claude-writer.md`

**Before** (Chunk Start Prompt):
- `[집필 전 메모]`: 8 bullet (기능, carry-forward 3-5개, 공개/비공개 정보, 처리된/미처리 일, 보이스 압력, 주요 장면, 감정 앵커, 엔딩 훅)
- `[Drafting Surface]`: 11 bullet (잘 읽히게, 분위기보다 선명도, 첫 문장, 결합 이상, 전투, 대사, 위계, 공간 공유, 직전 화 carry-forward, 오프스크린 금지, 보고/허락)
- `[초안 후 자기점검]`: 10 bullet (기능, 첫 문단, 반복, 전투, 결합, 공간 공유, 대사 평탄화, 위계, 조연 지식, 오프스크린)

**After**:
- `[집필 전 메모]`: **3 bullet** (기능 1줄, carry-forward 3~5개, 엔딩 훅 1개). 나머지는 `compile_brief Live Drafting Cues`에서 자동 제공.
- `[Drafting Surface]`: **4원칙** (선명도 우선, 평이함, 대사 위계 먼저, carry-forward 존중). 각 원칙에 기존 bullet 2~3개를 통합.
- `[초안 후 자기점검]`: **3 bullet** (분량, 기능 수행, carry-forward 점프). 나머지 7개는 `unified-reviewer` 전담으로 명시.

추가 변경:
- **Chunk Start ↔ Continuation 동기화**: 직전 화 읽기 분량을 둘 다 "마지막 장면 전체 또는 마지막 8~12문단 (최소 2~3문단)"으로 통일. 둘 다 3개 메모 / 4원칙 / 3개 자기점검 동일.
- **Sentinel 포맷 명시**: `{NN}은 2자리 0-padded (예: chapter-05.md, chapter-12.md)` 추가. 이전에는 supervisor가 `chapter-5.md` vs `chapter-05.md` 매칭 실패 가능성.
- **"질문하지 말고 자율 완료"**에 판단 가이드 추가: "판단 모호한 표기는 `summaries/style-lexicon.md` 우선 참조. 없으면 한자어/전통어 우선 선택" — review → fix 루프 감소 목적.
- **회귀/환생 POV 예외** 추가: "비현대 배경이면 외래어/아라비아 숫자를 쓰지 않는다 (회귀/환생 POV의 현대 내면 독백은 예외)". pov-era-checker의 예외가 writer prompt에 미반영이던 drift 해소.

#### `.claude/prompts/codex-writer.md`

claude-writer.md와 동일 구조로 동기화. 단, Codex 고유 특징 보존:
- 전투 장면 묘사 원칙("숫자를 세는 듯한 문장, 결과만 요약하는 문장" 경고 문구)을 §1 선명도 내에 유지.

### B. compile_brief.py 출력 버그 수정

#### B1. dialogue-log 테이블 헤더/구분선 누락 (L596-602)

**Before**:
```python
dialogue_rows = [
    line.strip() for line in dialogue_log.splitlines()
    if line.strip().startswith("|") and not line.strip().startswith("|----")
][:4]
if len(dialogue_rows) > 1:
    blocks.append("### 대사 운용 경고\n\n" + "\n".join(dialogue_rows))
```

헤더 행만 있고 구분선이 빠져서 마크다운 테이블로 인식되지 않음.

**After**: 첫 줄을 헤더로 간주하여 자동 구분선 삽입. `col_count`는 pipe 갯수로 계산.

#### B2. 관계 전환점 중복 출력 제거 (L604-606, L2034)

`_extract_relationship_turning_points`가 `_build_live_drafting_cues` (Live Cues 섹션) + `_compile_brief` (전역 컨텍스트 섹션) 두 곳에서 호출되어 동일 내용이 같은 brief에 2회 노출.

**After**: Live Cues 호출 제거. 전역 컨텍스트에만 유지. 근거: 관계 전환점은 historical reference 성격이라 "active drafting cue"가 아닌 "context" 쪽이 적절.

#### B3. promise-tracker status → due date 오표시 (L1053-1080)

**Schema** (빈 문자열 제거 후): `[ID, 당사자, 내용, 투하, 예정회수, 우선순위, 상세]`

**Before**:
```python
status = cols[4] if len(cols) > 4 else ""   # 실제로는 예정회수
...
f" [{status}]{latest}"   # [3화] 처럼 due date가 상태로 표시
```

**After**: `status` 변수명을 `due`로 교체. 출력은 `[priority / 마감 due]` 포맷 — 이전 `[3화]` → `[high / 마감 3화]`. 우선순위가 없으면 `[마감 3화]`만.

#### B4. 관계 전환점 테이블 헤더 추출 (L1684-1709)

**Before**: 원본 `relationship-log.md`의 테이블 헤더가 누락된 채 데이터 행만 출력 → LLM이 컬럼 의미 추론 불가.

**After**: 함수 초반에 원본 테이블의 헤더+구분선 행을 찾아서 결과 앞에 prepend. 헤더 없으면 데이터만 출력 (기존 동작 유지).

#### B5. term-onboarding 테이블 헤더 추가 (L2165-2181)

**Before**:
```python
sections.append(
    "## 용어 온보딩 경고\n\n"
    + "\n".join(overdue_lines[:10])
)
```

**After**: default header + separator 삽입:
```
| 용어 | 첫 등장 | 설명 완료 | 설명 기한 | 위험도 | 비고 |
|------|--------|----------|----------|--------|------|
```

#### B6. 브리프 크기 계산 오차 (L2183-2201)

**Before**: `size_kb = len(brief.encode("utf-8")) / 1024`가 `header_line` 삽입 **전** brief로 계산 → 헤더 포함된 실제 출력 크기보다 살짝 낮게 보고.

**After**: placeholder 방식으로 해결. 헤더에 `__BRIEF_SIZE_PLACEHOLDER__KB` 삽입 → 전체 join 후 실제 크기 계산 → placeholder 치환.

#### B7. `_estimate_source_size` 포함 파일 확장 (L2253)

**Before**: 9개 파일만 포함 (summaries 6개 + plot 1개 + CLAUDE.md + style-guide).
**After**: 20개로 확장 — dialogue-log, decision-log, review-log, style-lexicon, repetition-watchlist, desire-state, signature-moves, term-onboarding, 03-characters, 04-worldbuilding, 05-continuity 추가. 사용자가 "왜 brief가 큰가" 디버깅 시 더 정확한 수치 제공.

#### B8. 골든 스냅샷 재생성

위 수정으로 `tests/golden/brief-ep2.md` 변경 필요. 스크립트로 재생성:
```bash
python3 -c "
import sys; sys.path.insert(0, 'tests')
import tempfile
from pathlib import Path
import compile_brief
from test_compile_brief import make_novel
with tempfile.TemporaryDirectory() as td:
    novel_dir = make_novel(Path(td))
    brief = compile_brief._compile_brief(str(novel_dir), 2)
    Path('tests/golden/brief-ep2.md').write_text(brief + '\n', encoding='utf-8')
"
```

### C. `scripts/validate-settings.py` — 파일 누락 방어

**Before**: `.read_text(...)` 직접 호출 → 파일 없으면 Python traceback. supervisor 배치가 hard-stop.

**After**: `_safe_read(path, label, failures)` 헬퍼 도입. `FileNotFoundError` / `OSError` 잡아서 `failures` 리스트에 기록, 빈 문자열 반환. 다른 검증은 계속 진행 후 `FAIL` 라인 집계 출력.

### D. `scripts/event-log.py` — float coerce 추가

**Before**: `_coerce`가 bool / null / int → string. 숫자 `duration=1.5` 전달 시 string으로 저장.
**After**: int 실패 시 float 시도. 모두 실패하면 string.

## Rollback

### 전체 Phase 1 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-1-commit-sha>
```

### 개별 롤백

**Writer prompt만 복구**:
```bash
git checkout <pre-phase-1-sha> -- .claude/prompts/claude-writer.md .claude/prompts/codex-writer.md
```

**compile_brief.py만 복구**:
```bash
git checkout <pre-phase-1-sha> -- compile_brief.py tests/golden/brief-ep2.md
```

**validate-settings.py만 복구**:
```bash
git checkout <pre-phase-1-sha> -- scripts/validate-settings.py
```

**event-log.py만 복구**:
```bash
git checkout <pre-phase-1-sha> -- scripts/event-log.py
```

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. 테스트 전체 통과
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed

# 2. Writer prompt 다이어트 확인
grep -c "^1\." .claude/prompts/claude-writer.md   # 여러 "1." 불릿 있지만
grep -A1 "집필 전 메모" .claude/prompts/claude-writer.md | head -3
# → "3개만"이 포함되어야

# 3. compile_brief 출력 확인
python3 -c "
import sys; sys.path.insert(0, 'tests')
import tempfile
from pathlib import Path
import compile_brief
from test_compile_brief import make_novel
with tempfile.TemporaryDirectory() as td:
    novel_dir = make_novel(Path(td))
    brief = compile_brief._compile_brief(str(novel_dir), 2)
    # Promise tracker가 [3화]가 아니라 [high / 마감 3화]
    assert '[high / 마감 3화]' in brief
    # 용어 온보딩 테이블에 헤더 존재
    assert '| 용어 | 첫 등장' in brief
    # 관계 전환점에 테이블 헤더
    assert '### 관계 전환점' in brief
    print('compile_brief 출력 검증 통과')
"

# 4. validate-settings 파일 누락 방어
python3 scripts/validate-settings.py --novel-dir /tmp/nonexistent 2>&1
# → 'FAIL ... missing file' 출력, traceback 없음, exit code 1

# 5. event-log float coerce
python3 scripts/event-log.py /tmp/test-nov-$$ test_event duration=1.5
# → 레코드에 "duration": 1.5 (float)
```

## Dependencies

**선행**: Phase 0 (Spec Canon에 sentinel 포맷 명시가 Phase 1 writer prompt의 "{NN}은 2자리 0-padded" 지시의 근거).

**후행**:
- Phase 2: 평탄화 차단 작업이 writer prompt의 `[Review Surface]` 섹션을 추가 수정. Phase 1가 구조를 단순화했기에 Phase 2 수정 지점이 명확.
- Phase 3: narrative-fixer 재정의 시 writer prompt의 `[금지]` 섹션 내 `FIX_DONE` vs `WRITER_DONE` 분리 이슈 해결.

## Known Issues / Follow-ups

1. **Substring character matching** (`any(char in name for char in characters)` — L790, 862, 937-938, 956, 988, 1374, 1965): 단자 이름("白" 등)에서 오탐 위험 남음. Phase 1는 출력 버그만 수정. 문자 매칭 개선은 별도 이슈로 분리.
2. **Golden snapshot의 취약성**: 테스트가 전체 11KB brief를 byte-exact로 락. 의미 단위 assert 테스트 추가는 Phase 5로 연기.
3. **Writer prompt의 "판단 가이드"가 `style-lexicon.md`에만 의존**: `style-lexicon.md`가 비어 있는 신규 프로젝트에서는 fallback("한자어 우선")이 항상 발동. Phase 2 voice preservation 시 style-lexicon 초기 seed 절차 개선.
4. **`_estimate_source_size`는 여전히 paths hardcoded**: compile_brief가 읽는 파일 목록과 별개로 유지됨. 향후 `_compile_brief`에서 실제 읽은 파일 리스트를 기반으로 계산하도록 리팩토링 가능.
5. **`codex-fixer.md`, `claude-fixer.md`**는 이번 phase에서 건드리지 않음. Phase 3 narrative-fixer 재정의 시 함께 처리.

## References

- 원 리뷰: Phase 1 대상 문제들은 python-pro, prompt-engineer, general-purpose 에이전트의 지적에서 선별.
- 영향 파일: `.claude/prompts/claude-writer.md`, `.claude/prompts/codex-writer.md`, `compile_brief.py`, `scripts/validate-settings.py`, `scripts/event-log.py`, `tests/golden/brief-ep2.md`
