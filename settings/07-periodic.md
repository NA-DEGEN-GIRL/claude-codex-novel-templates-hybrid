# Parallel Writing & Periodic Checks

> 정기 점검 규약. 매 화 파이프라인이 놓치기 쉬운 누적 드리프트를 제어한다.

**Language Contract: All narrative output, summaries, and review text MUST be in Korean.**

---

## 1. Post-Parallel-Writing Consistency Check

동시 집필 또는 summary 지연이 있었으면, 병렬 작성 종료 후 아래 절차를 강제한다.

### Parallel Writing Criteria

- 여러 agent/session이 다른 화를 동시에 집필
- 연속 화가 존재하지만 summary가 뒤늦게 갱신됨
- 사용자가 병렬 집필 중이라고 명시

### Per-Agent Rules

- 각 작성자는 자신의 할당 범위 안에서 초안과 1차 self-review를 끝낸다.
- 병렬 작성 중에는 summary 충돌을 막기 위해 필수 summary 갱신을 마지막 reconciliation까지 미뤄도 된다.
- `EPISODE_META`는 각 화에 정상 삽입한다.

### Reconciliation

1. 낮은 화수부터 높은 화수 순으로 본문 연결 확인
2. higher episode를 lower episode에 맞춰 조정
3. `running-context.md`, `episode-log.md`, `character-tracker.md`를 화수 순으로 일괄 갱신
4. `review-log.md`와 `action-log.md`에 병렬 정리 결과 기록

---

## 2. Periodic Checks

### Trigger

- 기본 5화 단위
- 최대 8화 초과 금지
- 아크 전환에서는 무조건 실행
- 드리프트 징후나 작가 판단이 있으면 조기 실행

### Review Floors

- 1화 또는 새 아크 첫 화: `full`
- 5화 배수: `standard`
- 아크 마지막 화: `standard + arc transition package`

### Check Items

Core 항목은 매번 실행한다. Optional은 관련이 있을 때만 수행한다.

| # | Item | Type | Method |
|---|---|---|---|
| P1 | Summary consistency | Core | 최근 점검 이후 화수의 본문과 `running-context`, `episode-log`, `character-tracker` 불일치 탐지. 시간축, 나이, 경과일수, 부상/이동/수련 기간 모순도 함께 본다 |
| P2 | Foreshadowing deadlines | Optional | `plot/foreshadowing.md`에서 회수 시점 경과 여부 확인 |
| P3 | Character state freshness | Core | `character-tracker.md`가 최신 화 종료 상태를 반영하는지 확인 |
| P4 | Unfulfilled promises | Optional | `promise-tracker.md`에서 과잉 유예 또는 방치 약속 탐지 |
| P5 | running-context hygiene | Optional | `running-context.md`가 과팽창하지 않았는지, 다음 화 런웨이가 선명한지 확인 |
| P6 | Personality drift vs growth | Core | 성격 변화가 사건 기반인지 확인. 일시적 퇴행과 동요도 사건 근거가 있으면 허용 |
| P7 | WHY/HOW + motivation-action gap | Core | 최근 5화 재독으로 설명 갭, 동기/행동 갭, OAG 의심 탐지 |
| P8 | External batch review | Optional | 프로젝트가 외부 리뷰를 켠 경우에만 템플릿의 batch review 또는 episode review 도구를 실행하고, 비활성 프로젝트에서는 건너뛴다 |
| P9 | POV / era / scene logic | Core | 시점 지식 위반, 시대 부적합 표현, 장면 물리·인과 논리 점검 |
| P10 | Cross-episode repetition | Core | 어구, 감정 처리, 정보 재노출, 엔딩 훅 반복 패턴 탐지 |
| P11 | Korean naturalness | Core | 번역투, 호응, 템포 저하, 장면별 어색한 문장 정리 |
| P12 | Meta-reference prohibition | Core | 본문 속 `몇 화에서`, `프롤로그에서`, `1부에서` 금지 표현 탐지 |
| P13 | Thematic progress | Core | 최근 화수의 `thematic_function`과 실제 본문이 같은 방향을 가는지 대조하고, 주제 진행이 끊긴 구간을 경고 |

### Mandatory Order

정기 점검 수정은 아래 순서로 한다.

1. summary consistency
2. fact / continuity, including time / age / duration consistency
3. WHY/HOW + motivation-action
4. POV / era / scene logic
5. repetition
6. Korean naturalness
7. external review reconciliation (if used)
8. summary re-sync

### Post-Check Actions

1. patch-feasible 항목은 즉시 수정
2. 구조 수정이 필요한 항목은 `review-log.md`에 HOLD 기록
3. `running-context.md`를 현재 상태로 갱신
4. 반복 패턴이 발견되면 `repetition-watchlist.md` 갱신
5. `action-log.md`에 점검 결과 append
6. commit 메시지 예시: `{소설명} {N}~{M}화 정기 점검 완료`

---

## 3. Arc Transition Link

아크 마지막 화 이후에는 이 문서만으로 끝내지 않는다.

반드시 아래를 이어서 수행한다.

1. 템플릿의 아크 전환 절차(`batch-supervisor.md` 또는 프로젝트 체크리스트)를 이어서 실행
2. 아크 종료 범위를 다시 읽고 WHY/HOW 설명 갭, 동기/행동 갭, 미해결 약속, 반복 패턴을 점검
3. `patch-feasible` 항목은 즉시 수정하고, 구조 수정이 필요한 항목은 `review-log.md`에 `HOLD`로 기록
4. 본문 수정이 있었다면 영향 받은 summary와 tracker를 재정합
5. 다음 아크 plot readiness를 확인하고, `forward-fix`와 다음 화 런웨이를 `running-context.md`에 반영

---
