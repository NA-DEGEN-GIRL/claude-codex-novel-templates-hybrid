# Hybrid Template Implementation Log

이 문서는 `IMPROVEMENT-REPORT-V2.md`를 실행 명세로, `CODEX-TEMPLATE-IMPROVEMENT-REPORT.md`를 범위/순서 가드레일로 삼아 수행한 실제 패치 기록이다.

## 구현 순서

1. runtime integrity
2. compile_brief contract test
3. drafting surface split
4. handoff / authority / risk cleanup

## Commit Inventory

| Commit | 제목 | 핵심 범위 |
|--------|------|-----------|
| `b096b3f` | `Harden runtime integrity and review gate` | `_safe_read` 관찰성, `events.jsonl`, brief snapshot, `tmux-wait-sentinel` file fallback, `verify-review-done.py`, writer sentinel file 생성 |
| `0f60ee8` | `Add compile_brief contract tests and validator` | `tests/test_compile_brief.py`, `tests/golden/brief-ep2.md`, `validate-settings.py`, parser drift fix |
| `f6b43e5` | `Split drafting surface from review surface` | `Live Drafting Cues` 정제, writer prompt의 `Drafting Surface / Hard Rules / Review Surface` 분리, style guide writer/reviewer view 명시 |
| `e883a87` | `Close handoffs and clarify authority rules` | `resolution_threshold`, `Voice Profile Freshness` handoff, `settings/03-characters.md` pragmatic field 보강, `CLAUDE.md` / `README.md` 권위 정리 |
| `9f64d74` | `Add runtime helper instrumentation and operations scripts` | `tmux-send-*` / `tmux-wait-sentinel` 이벤트 로깅, `check-open-holds.py`, `summarize-runtime-metrics.py`, `suggest-voice-profile-refresh.py` |
| `e70e930` | `Extend live cues with HOLD and live field support` | `compile_brief` HOLD 경고 / live fields, `desire-state.md`, `signature-moves.md`, `batch-supervisor` preflight, validator 확장 |

## Patch Summary

### 1. Runtime Integrity

- `compile_brief.py`
  - `tmp/run-metadata/events.jsonl` 이벤트 기록 추가
  - 읽기 실패 로그(`read-errors.log`) 지원
  - `tmp/briefs/chapter-{NN}.md` snapshot 저장
- `scripts/tmux-send-claude`
  - `Compacting` 오인 응답 제거
- `scripts/tmux-wait-sentinel`
  - 기본 capture window `500`
  - optional sentinel file fallback 추가
- `scripts/verify-review-done.py`
  - staged/HEAD 모드 review gate 추가
- writer prompt
  - `tmp/sentinels/chapter-{NN}.done` 생성 규칙 추가
- `batch-supervisor.md`
  - send helper 성공 확인 → sentinel wait 순서 고정
  - `REVIEW_DONE` 전 helper gate 명시

### 2. Contract Tests

- `tests/test_compile_brief.py`
  - synthetic novel fixture 기반 11개 테스트
  - previous-anchor missing, ending-hook extraction, decision-log omission, watchlist filtering, notation fallback 검증
- `tests/golden/brief-ep2.md`
  - episode 2 compile output snapshot 고정
- `scripts/validate-settings.py`
  - `01-style-guide.md`, `03-characters.md`, `summaries/running-context.md` 구조 계약 점검

### 3. Drafting Surface Split

- `compile_brief.py`
  - `## Live Drafting Cues`를 목표/직전 장면/오프닝 상태/보이스 우선순위/대사 경고/반복 경고 중심으로 재배치
- `.claude/prompts/codex-writer.md`
- `.claude/prompts/claude-writer.md`
  - `Drafting Surface`, `Hard Rules`, `Review Surface` 분리
  - 초안 단계에서 review checklist를 과잉 적용하지 말라는 운영 원칙 반영
- `settings/01-style-guide.md`
  - `Writer View` / `Reviewer View` 명시

### 4. Handoff / Authority / Risk

- `batch-supervisor.md`
  - `resolution_threshold` 추가
  - `Voice Profile Freshness` 경고의 arc-boundary handoff 추가
  - `prose_risk` / `emotion_risk` override 근거 문구 추가
- `settings/03-characters.md`
  - `말 길이 경향`, `회피 반응`, `대화 대비축` 필드 추가
- `CLAUDE.md`
  - `prose_risk`, `emotion_risk` 필드 추가
  - 문서 권위/우선순위 섹션 재작성
- `README.md`
  - 온보딩 문서라는 점과 runtime authority 경계 명시

### 5. Runtime Observability / HOLD Operations

- `scripts/tmux-send-claude`
- `scripts/tmux-send-codex`
- `scripts/tmux-wait-sentinel`
  - helper 시작/결과를 모두 `events.jsonl`에 기록
  - supervisor가 `SESSION_MISSING`, `WORKING_CONFIRMED`, `CLAUDE_RESPONSE_CONFIRMED`, `SENTINEL_FOUND`, `TIMEOUT`를 런타임 지표로 집계 가능
- `scripts/check-open-holds.py`
  - `review-log.md`의 `HOLD-*` 블록을 파싱해 overdue / blocker를 기계적으로 판정
  - `--fail-on-overdue`, `--fail-on-blocker`, `--format json|markdown|line` 지원
- `scripts/summarize-runtime-metrics.py`
  - `events.jsonl`을 읽어 read error, review gate, tmux helper 결과, brief size를 요약
- `scripts/suggest-voice-profile-refresh.py`
  - 최근 화 본문에서 §0.3 후보 문단을 점수화해 추출

### 6. Live Drafting Cues / Live Fields

- `compile_brief.py`
  - `running-context.md`의 `## HOLD 경고`를 집필 cue로 승격
  - `review-log.md`의 open HOLD를 `### OPEN HOLD 경고`로 노출
  - `summaries/desire-state.md`를 `### Desire State`로 노출
  - `summaries/signature-moves.md`를 `### Signature Moves`로 노출
  - `settings/01-style-guide.md` parser를 정리해 `### 시점` / `### 우선 원칙`이 중복 없이 나오도록 수정
- `summaries/desire-state.md`
  - `Current Desire / Current Anxiety / This Episode Touchpoints` 템플릿 추가
- `summaries/signature-moves.md`
  - `Opening / Pressure / Landing / Overused Moves` 템플릿 추가
- `batch-supervisor.md`
  - 화별 집필 전 `check-open-holds.py` preflight 추가
  - conditional summary 갱신 대상으로 `desire-state.md`, `signature-moves.md` 추가

### 7. Second-Wave Tests

- `tests/test_compile_brief.py`
  - live fields/HOLD cue 노출 검증
  - style parser 중복 회귀 검증 (`### 시점`, `### 우선 원칙`)
- `tests/test_runtime_helpers.py`
  - `check-open-holds.py`
  - `summarize-runtime-metrics.py`
  - `suggest-voice-profile-refresh.py`
  - tmux helper smoke test (sandbox에서는 socket 제한 시 skip)
- `tests/golden/brief-ep2.md`
  - HOLD/live fields/정리된 style parser 결과 반영

## Verification

실행한 검증:

```bash
python3 -m py_compile compile_brief.py scripts/event-log.py scripts/verify-review-done.py scripts/validate-settings.py
pytest -q tests/test_compile_brief.py
python3 scripts/validate-settings.py --novel-dir /root/novel/claude-codex-novel-templates-hybrid
python3 compile_brief.py /root/novel/claude-codex-novel-templates-hybrid 1
python3 -m py_compile scripts/check-open-holds.py scripts/summarize-runtime-metrics.py scripts/suggest-voice-profile-refresh.py tests/test_runtime_helpers.py
pytest -q tests/test_compile_brief.py tests/test_runtime_helpers.py
```

확인 결과:

- `pytest`: `11 passed`
- `validate-settings.py`: `VALID settings/running-context contract OK`
- `compile_brief.py` smoke run:
  - `tmp/briefs/chapter-01.md` 생성 확인
  - `tmp/run-metadata/events.jsonl` 생성 확인
- second-wave `pytest`: `15 passed, 3 skipped`
  - skip 이유: sandbox 내부에서는 tmux socket 생성이 차단될 수 있어 helper smoke를 조건부 skip
- escalated tmux smoke:
  - `tmux-send-claude` → `CLAUDE_RESPONSE_CONFIRMED`
  - `tmux-send-codex` → `WORKING_CONFIRMED`
  - `tmux-wait-sentinel` → `SENTINEL_FOUND mode=file_fallback`
  - 세 helper 모두 `events.jsonl` 기록 확인

## Notes

- prompt 파일과 `batch-supervisor.md`에는 이미 존재하던 로컬 변경이 있었고, 해당 변경을 되돌리지 않고 이번 패치에 흡수했다.
- `tmp/briefs/`, `tmp/run-metadata/`, `tmp/sentinels/`, `.pytest_cache/`는 `.gitignore`에 추가했다.
- 구현 범위는 pilot 이전까지다. 실제 연재 파일럿/지표 측정은 별도 운영 단계로 남는다.
- second-wave부터는 `IMPROVEMENT-REPORT-V2.md`를 실행 명세, `CODEX-TEMPLATE-IMPROVEMENT-REPORT.md`를 범위 가드레일로 사용했다.
