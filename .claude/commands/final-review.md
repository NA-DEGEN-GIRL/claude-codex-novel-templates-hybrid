소설 완결 후 최종 검증 파이프라인을 실행한다. 3단계로 나뉘어 순차 실행.

## 사용법

```
/final-review          # 현재 상태 확인 + 다음 단계 안내
/final-review analyze  # Phase A~B: 독립 분석 + 통합 진단
/final-review fix      # Phase C~D: 서사 수정 + 재검증
/final-review audit    # Phase E: 사실 검증 + 교정
```

## 파이프라인 개요

```
Phase A~B (analyze):  why-check full + book-review 2종 + narrative-review
Phase C~D (fix):      narrative-fix + why-check delta + why-fix
Phase E (audit):      audit + audit-fix
```

## 실행

### `/final-review` (인자 없음)

현재 진행 상태를 확인하고 다음 단계를 안내한다.
- `summaries/final-review-state.md` 파일을 읽어 어디까지 완료됐는지 확인
- 파일이 없으면 "analyze부터 시작하세요" 안내
- 완료된 Phase가 있으면 "다음은 {phase}입니다" 안내

### `/final-review analyze` (Phase A~B)

**Phase A: 독립 분석 (병렬)**
1. `/why-check full` 실행 → `summaries/why-check-report.md`
2. `/book-review` 실행 → `summaries/book-review.md`
   - 1~3은 가능하면 병렬 (Agent 활용)

**Phase B: 통합 진단**
4. `/narrative-review` 실행 → `summaries/narrative-review-report.md`
   - Phase 4에서 1~3의 보고서를 자동 참조

**완료 후**: `final-review-state.md`에 "analyze: DONE" 기록. 결과 요약 출력.


### `/final-review fix` (Phase C~D)

**전제**: analyze 완료. `narrative-review-report.md` 존재해야 함.

**Phase C: 서사 수정**
5. `/narrative-fix` 실행 — fix guide 항목 수정 (S1~S6)
   - **수정 전 계획을 사용자에게 보여주고 승인 받기**

**Phase D: 수정 후 재검증**
6. 수정된 화수 + 인접 1화에 대해 `/why-check` delta-check
7. still-missing 항목에 `/narrative-fix --source why-check` (E1~E4)

**완료 후**: `final-review-state.md`에 "fix: DONE" 기록. 수정 건수 요약.

> ✅ 완료 기준: narrative-fix-log.md 존재 + delta-check 완료

### `/final-review audit` (Phase E)

**전제**: fix 완료.

**Phase E: 사실 검증 + 교정**
8. `/audit` 실행 → `summaries/full-audit-report.md` (Korean naturalness는 audit Phase 2.5에 내장)
9. `/audit-fix` 실행 (이슈 있을 때만)

**완료 후**: `final-review-state.md`에 "audit: DONE" 기록. 전체 완료 보고.

> ✅ 완료 기준: full-audit-report 존재

## 상태 파일

`summaries/final-review-state.md`:
```markdown
# Final Review State

| Phase | 상태 | 완료 시각 |
|-------|------|----------|
| analyze | DONE / PENDING | {timestamp} |
| fix | DONE / PENDING | {timestamp} |
| audit | DONE / PENDING | {timestamp} |

## 산출물
- why-check-report.md: ✅
- book-review.md: ✅
- narrative-review-report.md: ✅
- narrative-fix-log.md: ✅
- full-audit-report.md: ✅
```

## 주의

- **analyze → fix → audit 순서 필수.** 이전 Phase가 완료되지 않으면 다음 Phase 실행 거부.
- **fix Phase에서 사용자 승인 필수.** narrative-fix 계획을 보여주고 승인 후 실행.
- 각 Phase는 독립 세션에서 실행 가능. 상태 파일로 재개.
- batch-supervisor.md의 "On final completion" 섹션과 동일한 파이프라인. 수동 실행용 인터페이스.
