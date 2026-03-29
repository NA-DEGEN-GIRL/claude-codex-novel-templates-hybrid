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

### Design Principle

- **약한 안전장치를 자주, 강한 진단기는 드물게.**
- `review_floor`와 specialist checker cadence를 분리한다.
- `standard` review를 실행한다고 해서 `why-check`, `oag-check`, `pov-era-check`, `scene-logic-check`, `repetition-check`를 자동 실행하지 않는다.
- specialist checker는 화수 고정 주기보다 **위험 신호(risk signal)**를 우선 트리거로 삼는다.
- periodic의 목적은 초안을 다시 쓰게 만드는 것이 아니라, **누적 drift를 조기에 잡고 다음 구간에서 더 크게 망가지지 않게 하는 것**이다.
- 검사 규칙은 초안 생성 규칙을 오염시키지 않는다. patch-feasible한 사실 오류와 장면 로컬 문제는 즉시 수정하되, 설명/동기/반복/주제 문제는 기본적으로 `watch`, `forward-fix`, `HOLD`를 우선 검토한다.

### Trigger

- 기본 periodic `standard` 점검은 **6~8화 단위**로 실행한다.
- 기본값은 **7화 간격**으로 잡되, **8화를 초과해서 미루지 않는다**.
- 아크 전환에서는 무조건 실행한다.
- 아래 중 하나라도 보이면 조기 실행할 수 있다:
  - 최근 2~3화에서 연속으로 continuity warning이 누적됨
  - summary/tracker drift가 의심됨
  - 문장 자연스러움 저하가 반복됨
  - 같은 장면 기능/엔딩 훅/감정 처리 패턴이 계속 겹침
  - 사용자가 drift나 품질 저하를 명시적으로 지적함

### Review Floors

- 1화 또는 새 아크 첫 화: `full`
- 일반 화: `continuity`
- periodic due 시점: `standard`
- 아크 마지막 화: `standard + arc transition package`
- 아래 조건에서는 화수와 무관하게 `full`까지 올릴 수 있다:
  - 대형 설정 전환
  - 장기 복선의 핵심 회수
  - 세계 규칙 해석이 크게 바뀌는 화
  - review 세션이 "이번 화는 direct settings reference가 없으면 판정이 위험하다"고 판단한 경우

### Check Layers

정기 점검은 **Core layer**와 **Conditional layer**로 나눈다.

#### Core layer

| # | Item | Type | Method |
|---|---|---|---|
| P1 | Summary consistency | Core | 최근 점검 이후 화수의 본문과 `running-context`, `episode-log`, `character-tracker` 불일치 탐지. 시간축, 나이, 경과일수, 부상/이동/수련 기간 모순도 함께 본다 |
| P3 | Character state freshness | Core | `character-tracker.md`가 최신 화 종료 상태를 반영하는지 확인 |
| P5 | running-context hygiene | Core | `running-context.md`가 과팽창하지 않았는지, 다음 화 런웨이가 선명한지 확인 |
| P6 | Personality drift vs growth | Core | 성격 변화가 사건 기반인지 확인. 일시적 퇴행과 동요도 사건 근거가 있으면 허용 |
| P11 | Korean naturalness | Core | 번역투, 호응, 템포 저하, 장면별 어색한 문장 점검. 단, 보이스 평탄화보다 오탐 방지를 우선한다 |
| P12 | Meta-reference prohibition | Core | 본문 속 `몇 화에서`, `프롤로그에서`, `1부에서` 금지 표현 탐지 |

#### Conditional layer

| # | Item | Type | Trigger |
|---|---|---|---|
| P2 | Foreshadowing deadlines | Optional | 회수 시점이 임박했거나 deadline drift가 의심될 때 |
| P4 | Unfulfilled promises | Optional | 약속/기한/예고가 최근 화수에서 반복적으로 밀릴 때 |
| P7 | WHY/HOW + motivation-action gap | Conditional | 고위험 장면, 설명 누락 의심, 후폭풍 부재, 수동 주인공 패턴 누적 시 |
| P8 | External batch review | Optional | 프로젝트가 외부 리뷰를 켠 경우에만 |
| P9 | POV / era / scene logic | Conditional | 용어/시점/시대/전투/동선이 실제로 위험한 화수일 때만 전담 checker 호출 |
| P10 | Cross-episode repetition | Conditional | watchlist 누적, 같은 패턴 재등장, 아크 경계, 또는 8~15화 간격 점검 시 |
| P13 | Thematic progress | Optional | 최근 화수의 `thematic_function`과 실제 본문 괴리가 반복될 때. 정밀 진단은 아크 경계 우선 |
| P14 | Dialogue carriage & relationship pressure | Optional | 관계 장면 비중이 높은 작품/구간일 때 |
| P15 | Pressure-release rhythm | Optional | 최근 화수가 계속 같은 압력 톤으로만 눌릴 때 |
| P16 | Co-presence / off-screen logic | Optional | 동행/은신/합숙/공동 경계 상황이 자주 나올 때 |

### Specialist Cadence

| Agent / Check | Cadence |
|---|---|
| `unified-reviewer continuity` | 매 화 |
| `unified-reviewer standard` | 6~8화 주기 또는 조기 drift trigger |
| `unified-reviewer full` | 새 아크 첫 화 / 대형 설정 전환 / 장기 복선 핵심 회수 / severe drift |
| `why-check` | 기본 상시 아님. 설명 누락 의심 구간, 고위험 장면, 아크 전환에서 실행 |
| `oag-check` | 기본 상시 아님. 구조상 당연한 행동 기대가 강한 장면, 아크 전환에서 실행 |
| `pov-era-check` | 전근대/무협/회귀/시스템 용어 위험 화수, 지식 누수 의심 화수, 아크 경계 |
| `scene-logic-check` | 전투/추격/블로킹 복잡 장면, 아크 경계 |
| `repetition-check` | 8~15화 간격 또는 아크 경계. watchlist가 없으면 더 늦춰도 된다 |
| `narrative-review` | 아크 경계 또는 품질 저하 의심 시 |
| `full-audit` | 장기 구간 종료 또는 출판 전 |
| `book-review` | 아크 완결/완결 후 독자 관점 점검 |

### Mandatory Order

정기 점검 수정은 아래 순서로 한다.

1. summary consistency
2. fact / continuity, including time / age / duration consistency
3. Korean naturalness의 명백한 surface 문제
4. running-context / tracker hygiene
5. Conditional layer 중 실제 trigger가 켜진 항목만 수행
6. summary re-sync

> `WHY/HOW`, `OAG`, `repetition`, `thematic progress`는 trigger가 없는 한 기본 패키지에 자동 포함하지 않는다.

### Post-Check Actions

1. 즉시 수정:
   - summary fact conflict
   - definite continuity conflict
   - 명백한 Korean surface error
   - patch-feasible한 장면 로컬 문제
2. 기본적으로 즉시 대수선하지 않음:
   - WHY/HOW gap
   - motivation-action gap
   - repetition
   - thematic drift
   - relationship pressure weakness
3. 위 항목들은 우선 `watch`, `forward-fix`, `HOLD` 중 하나로 분류한다.
4. 반복 패턴이 발견되면 `repetition-watchlist.md` 갱신
5. `running-context.md`를 현재 상태로 갱신
6. `action-log.md`에 점검 결과 append
7. commit 메시지 예시: `{소설명} {N}~{M}화 정기 점검 완료`

---

## 3. Arc Transition Link

아크 마지막 화 이후에는 이 문서만으로 끝내지 않는다.

반드시 아래를 이어서 수행한다.

1. 템플릿의 아크 전환 절차(`batch-supervisor.md` 또는 프로젝트 체크리스트)를 이어서 실행
2. 아크 종료 범위를 다시 읽고 WHY/HOW 설명 갭, 동기/행동 갭, 미해결 약속, 반복 패턴을 점검
3. `patch-feasible` 항목은 즉시 수정하고, 구조 수정이 필요한 항목은 `review-log.md`에 `HOLD`로 기록
4. 본문 수정이 있었다면 영향 받은 summary와 tracker를 재정합
5. 다음 아크 plot readiness를 확인하고, `forward-fix`와 다음 화 런웨이를 `running-context.md`에 반영
