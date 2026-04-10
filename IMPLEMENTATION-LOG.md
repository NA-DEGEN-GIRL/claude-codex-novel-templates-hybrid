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

## Verification

실행한 검증:

```bash
python3 -m py_compile compile_brief.py scripts/event-log.py scripts/verify-review-done.py scripts/validate-settings.py
pytest -q tests/test_compile_brief.py
python3 scripts/validate-settings.py --novel-dir /root/novel/claude-codex-novel-templates-hybrid
python3 compile_brief.py /root/novel/claude-codex-novel-templates-hybrid 1
```

확인 결과:

- `pytest`: `11 passed`
- `validate-settings.py`: `VALID settings/running-context contract OK`
- `compile_brief.py` smoke run:
  - `tmp/briefs/chapter-01.md` 생성 확인
  - `tmp/run-metadata/events.jsonl` 생성 확인

## Notes

- prompt 파일과 `batch-supervisor.md`에는 이미 존재하던 로컬 변경이 있었고, 해당 변경을 되돌리지 않고 이번 패치에 흡수했다.
- `tmp/briefs/`, `tmp/run-metadata/`, `tmp/sentinels/`, `.pytest_cache/`는 `.gitignore`에 추가했다.
- 구현 범위는 pilot 이전까지다. 실제 연재 파일럿/지표 측정은 별도 운영 단계로 남는다.
